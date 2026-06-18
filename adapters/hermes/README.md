# Hermes Adapter

Hermes is the first-class runtime for Overkill Factory.

The adapter hardens Hermes Kanban so Factory cards cannot move through the
production line unless their contracts are complete.

## Patch

```text
patches/0001-overkill-factory-v35-gates-official-main.patch
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
- Worker-result done gate for Product Face, Solana/Quasar Auditor, QA,
  independent review, human gate and optional remote proof.
- Auditor preflight cannot close onchain/Solana/Quasar work as a PASS; a real
  code-audit result must carry checklist coverage, instruction matrix, state
  model, known-vector coverage and Quasar toolchain proof.
- Correct CLI exit-code propagation.
- Dashboard direct `ready` and bulk `ready` validation, so a browser/API move
  cannot bypass the same Factory gate.
- Dashboard/API `done` failures return HTTP 409 with the gate reason.
- Worker CLI `done` failures return non-zero with the gate reason.
- Dispatch JSON reports spawned workers with task refs, run refs and worker PID
  when Hermes exposes them.
- Regression tests.

The base patch line was validated against official Hermes commit
`56236b16e383cc656bb8c88429902f4de83f1faf`. For current checkouts, run
`adapters/hermes/compatibility-check.py`; it verifies the patch is parseable and
that the required gate and dispatch-reporting markers are still present.

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

## Live Materialization

The live adapter can materialize the transition plan into Hermes tasks:

```bash
python adapters/hermes/live_kanban_adapter.py materialize \
  --card path/to/card.md \
  --board overkill-factory-live \
  --ledger path/to/worker-ledger.json \
  --receipt path/to/receipt-five.json \
  --worker-results-dir path/to/worker-results \
  --route-readiness path/to/route-readiness.json
```

When a `BLOCKED` review produces a factory-owned `recovery_route`, the adapter
unblocks only the repair worker task authorized by that route. Downstream work
stays blocked until a fresh review result provides the stated unblock
authority. The adapter verifies Hermes readback after block/unblock operations;
it does not keep a parallel lifecycle state. Recovery retry attempts are derived
from stable `factory_recovery_attempt` markers in the Hermes task history for
that route before each unblock. If Hermes cannot return a task history source,
or if the route's `retry_policy.max_attempts` is exceeded, the adapter leaves
the task blocked and reports `recovery_retry_blocked_worker_task_ids`. If an
idempotent rerun finds the repair task already ready, running or done, the
adapter records an `already_active_no_new_attempt` no-op instead of blocking or
unblocking it again.

When that fresh review records a matching `PASS`, the adapter can reopen only
the explicitly authorized downstream worker ids from the transition plan. This
is not a broad card approval: satisfied producer/reviewer tasks stay closed for
execution purposes, `human-gate-clerk` stays blocked until real human evidence
exists, and the main card remains blocked until the normal completion gate
passes. Without `downstream_task_authorizations`, no downstream worker is
unblocked.

## Ready Work Unit Materialization Plan

Product dogfooding can reach a validated `ready_work_unit_packet_manifest`
before a legacy/card transition exists. In that case, build the Hermes
materialization plan first:

```bash
python scripts/factoryctl.py ready-work-unit-hermes-plan \
  --ready-work-unit-packets path/to/ready-work-unit-packets \
  --board overkill-factory-live \
  --out path/to/ready-work-unit-hermes-plan.json
```

The plan is not runtime execution proof and does not mutate Hermes. It defines
the exact runtime gate for each ready work unit using the
`create-unassigned-default-block-assign-v2` protocol: create the task without an
assignee and without `--initial-status blocked`, block it, verify a real
`blocked` event through Hermes readback,
assign the intended worker only after that blocked event exists, then verify
the task is still blocked and has no pre-dispatch `promoted`, `claimed`,
`spawned`, `spawn_failed` or run history. Dispatch happens only after that gate
evidence exists. Complete-product claims remain forbidden until all Product SOT
scope is reconciled through worker results, review and Receipt Five.

Ready work-unit packets and the resulting Hermes task contracts also carry both
a `context_boundary` and a resolved `work_unit_context_packet`. Workers may
inspect only named allowed refs plus artifacts created for the current
`work_unit_id`; broad repository archaeology is not a valid recovery path. The
packet must also include the owner worker's required inputs, such as
`done_definition`, `phase`, `risk_effective`, `surfaces`, rollback or
human-gate state when that profile requires them. If a required ref is only
named but not resolved through the context packet, validation blocks
materialization before dispatch. When context later becomes missing, stale,
forbidden or ambiguous, the task must block with owner instead of continuing
through unrelated history.
Use repeated `--forbidden-context-ref <public-safe-ref>` values when a live run
has known off-limits public refs, such as a separate issue or parallel product
thread.

When the runtime is reachable, the live adapter can consume that plan:

```bash
python adapters/hermes/live_kanban_adapter.py collect-route-readiness \
  --plan path/to/ready-work-unit-hermes-plan.json \
  --out path/to/route-readiness.json

python adapters/hermes/live_kanban_adapter.py materialize-ready-work-units \
  --plan path/to/ready-work-unit-hermes-plan.json \
  --route-readiness path/to/route-readiness.json \
  --workspace dir:<path-visible-to-hermes-dispatcher> \
  --out path/to/live-ready-work-unit-materialization-result.json

python adapters/hermes/live_kanban_adapter.py release-ready-work-units \
  --plan path/to/ready-work-unit-hermes-plan.json \
  --materialization-result path/to/live-ready-work-unit-materialization-result.json \
  --route-readiness path/to/route-readiness.json \
  --out path/to/released-ready-work-units.json
```

The collector is read-only: it derives required workers from the plan, checks
Hermes profiles and auth/provider readiness, and emits the official
`hermes-worker-route-readiness` manifest without embedding raw status dumps or
private paths. Materialization then creates blocked Hermes tasks only. It does
not dispatch workers, complete tasks, approve Receipt Five, or claim product
completion. Release verifies the materialization result, finds exactly one
blocked Hermes task per planned `packet_id`/`work_unit_id`, proves the real
`blocked` event, assignee, JSON body, dispatcher-visible workspace and absence
of pre-dispatch activity, records a Hermes-native audit comment with the
release markers, then unblocks those tasks to `ready`. Release accepts real
Hermes readback where the `unblocked` event itself has no payload as long as the
marker-bearing comment is present. Release does not dispatch workers; native
Hermes dispatch remains a separate command and the complete-product claim
remains forbidden.

If a ready work-unit task shows pre-dispatch runtime activity such as claim,
spawn, running state or run history before its dependency wave was legally
released, do not unblock it manually and do not reuse that runtime lineage. Run
the recovery path first:

```bash
python adapters/hermes/live_kanban_adapter.py recover-ready-work-units \
  --plan path/to/ready-work-unit-hermes-plan.json \
  --materialization-result path/to/live-ready-work-unit-materialization-result.json \
  --route-readiness path/to/route-readiness.json \
  --workspace dir:<path-visible-to-hermes-dispatcher> \
  --create-replacements \
  --out path/to/recovered-ready-work-units.json
```

Without `--create-replacements`, the command is a read-only recovery plan. With
it, the adapter preserves the contaminated task as blocked, records a
Hermes-native supersession marker, and creates a clean replacement with a new
idempotency lineage through the same blocked-first protocol. The old task
remains history; the replacement must still pass normal release, worker result,
review and Receipt Five gates before any product completion claim. The recovery
result is sanitized for public refs and always keeps
`complete_product_claim_allowed=false`.

After a legally released ready work unit executes and blocks, keep downstream
work units held and run post-release reconciliation instead of manually deciding
whether to retry or complete the parent:

```bash
python adapters/hermes/live_kanban_adapter.py reconcile-ready-work-units \
  --plan path/to/ready-work-unit-hermes-plan.json \
  --materialization-result path/to/live-ready-work-unit-materialization-result.json \
  --route-readiness path/to/route-readiness.json \
  --dry-run \
  --out path/to/reconciled-ready-work-units.json
```

The reconciliation path reads Hermes-authoritative task history and structured
repair/review markers. It keeps the parent blocked when repair or review proof
is incomplete, holds downstream dependencies until the parent is satisfied, and
escalates explicit human gates without automatic mutation. Without `--dry-run`,
it may unblock the parent only when review evidence carries
`ready_work_unit_repair_completed`, `ready_work_unit_repair_review_passed` and
`ready_work_unit_retry_authorized`; it may complete the parent only when the
history also carries `ready_work_unit_done_authorized` and
`ready_work_unit_done_definition_satisfied`. It still does not dispatch workers
or claim product completion.

If repair evidence exists but post-repair review markers are missing, the same
route can create the missing independent-reviewer task explicitly:

```bash
python adapters/hermes/live_kanban_adapter.py reconcile-ready-work-units \
  --plan path/to/ready-work-unit-hermes-plan.json \
  --materialization-result path/to/live-ready-work-unit-materialization-result.json \
  --route-readiness path/to/route-readiness.json \
  --create-post-repair-review-tasks \
  --out path/to/reconciled-ready-work-units.json
```

That task is scoped only to the repair result. It must emit
`ready_work_unit_repair_review_passed` plus either
`ready_work_unit_retry_authorized`, or `ready_work_unit_done_authorized` with
`ready_work_unit_done_definition_satisfied`, or `human_gate_required`, or a
structured BLOCK with owner and next repair action. Creating the review task
does not unblock or complete the parent.

Post-repair review cycles are versioned by repair evidence, not only by the
parent work unit. Reconciliation consumes structured parent markers first, and
may also consume Hermes `runs --json` metadata from independent-reviewer tasks
when the metadata identifies the parent task, reviewed repair card, validation
result, blocking findings and forbidden-approval flags. A repair-review PASS
without `ready_work_unit_retry_authorized` or `ready_work_unit_done_authorized`
is not enough to mutate the parent; the adapter reports
`awaiting_retry_or_done_authority` and keeps the work unit blocked. This lets a
blocked review route to repair and follow-up review without duplicate review
tasks or operator inference.

When reconciliation reaches `awaiting_retry_or_done_authority`, the adapter can
route the missing decision explicitly without mutating the parent:

```bash
python adapters/hermes/live_kanban_adapter.py reconcile-ready-work-units \
  --plan path/to/ready-work-unit-hermes-plan.json \
  --materialization-result path/to/live-ready-work-unit-materialization-result.json \
  --route-readiness path/to/route-readiness.json \
  --create-post-repair-authority-tasks \
  --out path/to/reconciled-ready-work-units.json
```

The authority task must emit retry, done, human-gate or structured-block
markers. Creating it does not dispatch, retry, complete, release or claim
product completion.

Use `--workspace` when the adapter runs outside the Hermes host. The workspace
must be meaningful to the Hermes dispatcher, not merely to the machine that runs
the adapter. Local operators can omit it and use the repo directory default;
remote operators should pass a dispatcher-visible `dir:<path>`, `worktree`, or
`scratch` reference intentionally.

## Dispatch Reporting

Hermes owns dispatch. The adapter does not schedule workers itself, but it can
wrap the native dispatch command and reconcile the immediate board state:

```bash
python adapters/hermes/live_kanban_adapter.py dispatch \
  --board overkill-factory-live
```

The response includes:

- `spawned_by_this_command`: workers reported by native Hermes dispatch;
- `already_running_after_dispatch`: workers that were ready before dispatch and
  running after dispatch, even if the native response reported `spawned: []`;
- `run_id` and `worker_pid` when Hermes exposes them;
- redacted workspace refs, never local absolute paths.

## Generated Transition Examples

Run the transition hook against `examples/minimal-hermes-project/card.md` to
generate local examples under `.tmp` or your CI temp directory:

- a ready-transition output demonstrates `allow_and_create_worker_tasks`;
- a done-transition output demonstrates reconciliation blocking when required
  worker results are still missing.

## Apply

From a Hermes checkout:

```bash
git switch -c codex/overkill-factory-10-gates
git apply /path/to/0001-overkill-factory-v35-gates-official-main.patch
python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
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

Real Hermes runtime integration is still not fully landed upstream. The public
adapter now provides the executable hook, ledger contract, CI smoke,
official-main-compatible Kanban patch, dashboard/API `ready` and `done` gate
rejection, and worker CLI completion rejection. The remaining work is to wire
Hermes Kanban events into this hook, map ledger tasks to real dashboard/API
worker cards, ingest worker result artifacts automatically, and prove full
specialist execution with real dispatched profiles.
