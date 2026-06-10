# Hermes Compatibility Manifest

Hermes is the first supported Overkill runtime. Updates must be treated as
adapter compatibility work, not as a casual package upgrade.

## Adapter Patch Families

```text
adapters/hermes/patches/0001-add-overkill-factory-10-kanban-gates.patch
adapters/hermes/patches/0002-add-overkill-vfinal-kanban-transition-hook.patch
adapters/hermes/patches/0003-materialize-overkill-vfinal-worker-subtasks.patch
adapters/hermes/patches/0004-guard-overkill-vfinal-dashboard-ready-route.patch
adapters/hermes/patches/0005-ingest-overkill-worker-results-from-subtasks.patch
adapters/hermes/patches/0006-fix-overkill-worker-subtask-dependency-direction.patch
adapters/hermes/patches/0007-add-dashboard-python-multipart-web-extra.patch
adapters/hermes/patches/0008-guard-overkill-vfinal-dashboard-delete-route.patch
adapters/hermes/patches/0009-guard-overkill-vfinal-dashboard-links-route.patch
adapters/hermes/patches/0010-guard-overkill-vfinal-dashboard-attachment-delete-route.patch
adapters/hermes/patches/0011-guard-overkill-vfinal-dashboard-bulk-archive-route.patch
adapters/hermes/patches/0012-guard-overkill-vfinal-dashboard-reassign-route.patch
adapters/hermes/patches/0013-guard-overkill-vfinal-dashboard-reclaim-terminate-routes.patch
adapters/hermes/patches/0014-guard-overkill-vfinal-dashboard-specify-route.patch
adapters/hermes/patches/0015-guard-overkill-vfinal-dashboard-decompose-route.patch
adapters/hermes/patches/0016-guard-overkill-vfinal-dashboard-board-delete-route.patch
```

`0001` is the legacy Factory 10 gate patch.

`0002` is an opt-in vFinal Kanban transition-gate patch for Hermes v0.16. It
must be validated against a clean Hermes `kanban_db.py` before any installed
runtime test.

`0003` is an opt-in worker-subtask materialization patch layered after `0002`.
It creates real Hermes tasks from the vFinal worker ledger only when
`OVERKILL_FACTORY_CREATE_WORKER_TASKS=1`. Production should keep
`OVERKILL_FACTORY_WORKER_TASK_STATUS=blocked` until worker-route parity and
worker-route readiness are proven.

`0004` guards dashboard/API `status=ready` so dashboard drag/drop and bulk
updates cannot bypass the vFinal transition gate.

`0005` ingests completed worker subtasks into parent worker-result artifacts for
done reconciliation.

`0006` fixes the worker-subtask dependency direction so workers are
prerequisites of the parent Factory card and can dispatch before the parent
closes.

`0007` adds the `python-multipart` dependency required by dashboard routes that
use FastAPI `File/Form` parameters.

`0008` guards dashboard/API `DELETE /tasks/{task_id}` so vFinal parent cards
and worker subtasks cannot be hard-deleted from the dashboard/API surface.

`0009` guards dashboard/API `POST /links` and `DELETE /links` so vFinal parent
cards and worker subtasks cannot have dependency links manually edited from the
dashboard/API surface.

`0010` guards dashboard/API `DELETE /attachments/{attachment_id}` so attachment
rows with tampered outside-root paths cannot delete arbitrary files.

`0011` guards dashboard/API `POST /tasks/bulk` with `archive=True` so vFinal
parent cards and worker subtasks cannot be hidden through bulk archive.

`0012` guards dashboard/API `POST /tasks/{task_id}/reassign` so vFinal parent
cards and worker subtasks cannot have execution profile changed manually.

`0013` guards dashboard/API `POST /tasks/{task_id}/reclaim` and
`POST /runs/{run_id}/terminate` so vFinal worker subtasks cannot be aborted by
generic recovery controls without an explicit operator-safe recovery workflow.

`0014` guards dashboard/API `POST /tasks/{task_id}/specify` so vFinal parent
cards and worker subtasks cannot have their task contract rewritten or promoted
through the generic auxiliary specifier route.

`0015` guards dashboard/API `POST /tasks/{task_id}/decompose` so vFinal parent
cards and worker subtasks cannot have a parallel task graph created through the
generic auxiliary decomposition route.

`0016` guards dashboard/API `DELETE /boards/{slug}` so boards containing vFinal
parent cards or worker subtasks cannot be archived or hard-deleted through
generic board controls.

Do not assume `0001`, `0002`, `0003`, `0004`, `0005`, `0006`, `0007`, `0008`,
`0009`, `0010`, `0011`, `0012`, `0013`, `0014`, `0015` and `0016` are a single linear patch stack. For the current
vFinal Hermes v0.16 validation path, apply `0002`, then `0003`, then `0005`,
then `0006` to a clean Hermes v0.16 `kanban_db.py`; apply `0004`, `0008`,
`0009`, `0010`, `0011`, `0012`, `0013`, `0014`, `0015` and `0016` to a clean Hermes v0.16
`plugins/kanban/dashboard/plugin_api.py`; and apply `0007` to the checkout
dependency files before dashboard smokes. A combined Factory 10 plus vFinal
runtime patch requires an explicit merge/port proof.

## Required Contract Versions

- `OVERKILL_V3_5_AGENT_WORKFORCE`
- `OVERKILL_V3_5_FACTORY_10`
- `OVERKILL_VFINAL`

## Required Symbols Across The Adapter Package

- `_overkill_is_v35_card`
- `_overkill_validate_v35_card`
- `_overkill_validate_v35_completion`
- `OVERKILL_VFINAL` support through the adapter transition hook and `factoryctl`
- `receipt_five`
- `kanban_transition_event`
- `security_scan_packet`
- `security_scan_result`
- `security_architecture_plan`
- `access_capability`
- `autonomy_readiness_packet`
- `factory_maturity_scorecard`
- `OverkillFactoryTransitionBlocked`
- `OVERKILL_FACTORY_KANBAN_GATE`
- `kanban_event_bridge.py`
- `overkill_factory_transition_gate`
- `overkill_factory_transition_blocked`
- `OVERKILL_FACTORY_CREATE_WORKER_TASKS`
- `overkill_worker_tasks_materialized`
- `materialized_worker_tasks`
- `overkill_worker_result_ingested`
- `worker_route_readiness.py`
- `worker_profile_readiness_smoke.py`
- `worker_dispatch_completion_smoke.py`

## Required Surfaces

- Hermes Kanban card validation before `ready`.
- Hermes completion validation before `done`.
- CLI exit-code propagation for blocked transitions.
- Dashboard/API `status=ready` routes must converge on the same gate logic.
- Factory cards cannot bypass the gate through direct `ready` creation.
- Factory cards cannot bypass the gate through automatic ready recompute.
- Factory cards cannot bypass the gate through unblock-to-ready.
- vFinal worker subtasks can be materialized as real Hermes tasks from the
  worker ledger in opt-in mode.
- Materialized worker subtasks default to blocked no-spawn state.
- Completed worker subtasks can persist worker-result artifacts for parent done
  reconciliation.
- Worker subtasks must link as prerequisites of the parent Factory card, so the
  parent waits for worker evidence and the workers can dispatch first.
- Worker-route readiness must block production dispatch when worker profiles,
  configs, models, providers or credential/reachable-local-endpoint evidence are
  missing.
- Local-stub worker profile readiness must prove disposable profile/config/
  model/provider shape and `/models` evidence before any production route is
  considered for `ready` workers.
- Synthetic dispatcher-completion must prove claim, completion and parent
  worker-result ingestion wiring in a disposable runtime.
- Real-process local-stub completion must prove the default dispatcher can
  spawn a real Hermes child process that calls `kanban_complete` and produces
  parent worker-result ingestion in a disposable runtime.
- Real-process matrix local-stub completion must prove that same child-process
  completion path for every vFinal worker route.
- Dashboard/API delete-route guard must block hard-delete for vFinal parent
  cards and worker subtasks.
- Dashboard/API links-route guard must block dependency-link edits that touch
  vFinal parent cards or worker subtasks.
- Dashboard/API attachment-route safety must block outside-root attachment
  deletion and prove safe traversal-name upload.
- Dashboard/API bulk archive must block vFinal parent cards and worker subtasks.
- Dashboard/API reassign must block execution-profile changes for vFinal parent
  cards and worker subtasks.
- Dashboard/API reclaim/terminate must block generic abort/recovery for vFinal
  worker subtasks unless an explicit operator-safe recovery workflow exists.
- Dashboard/API specify must block generic auxiliary rewriting/promotion for
  vFinal parent cards and worker subtasks.
- Dashboard/API decompose must block generic auxiliary task-graph fan-out for
  vFinal parent cards and worker subtasks.
- Dashboard/API comments must remain append-only for vFinal parent cards and
  worker subtasks; comments are operator notes, not authoritative gate evidence.
- Dashboard/API home-subscribe toggles must remain visibility-only for vFinal
  parent cards and worker subtasks; they route notifications but do not change
  task authority or contract state.
- Dashboard/API board archive/delete must block boards containing vFinal parent
  cards or worker subtasks unless an explicit operator-safe board retirement
  workflow exists.
- Dashboard/API board create, metadata patch and switch must remain operational
  metadata/current-board actions; they must not mutate existing vFinal task
  graphs, worker subtasks or dependency links.
- Dashboard/API profile patch and auto-description must remain profile metadata
  actions; they must not mutate existing vFinal task graphs, worker subtasks or
  dependency links. Auto-description proof may use a local stub for route safety
  and still must not claim real auxiliary model quality.
- Dashboard/API orchestration settings must remain Kanban configuration
  actions; they must not mutate existing vFinal task graphs, worker subtasks or
  dependency links. Missing profile overrides must be rejected before save.
- Real-runtime updates must run the production update preflight and remain
  blocked until operator control tower readiness and the complete update receipt
  are both proven. Local terminal-tool auth, scanner-backed specialist quality,
  real-worker parent reconciliation and real gateway rollback/monitoring have
  bounded PASS proofs, but they do not waive future card-specific external tool
  evidence or the package-level rollback plan in the update receipt.
- Real-runtime worker dispatch evidence must stay honest: bounded dispatch-only
  evidence remains `BLOCKED` until a separate terminal-completion receipt proves
  closure through the expected worker path.
- Real-runtime terminal completion evidence must include a live provider/model
  auth probe. Status-level auth output is not enough; a worker route that cannot
  make a live provider request must stay `BLOCKED`.
- Real-runtime profile auth matrix evidence must prove that every non-human
  vFinal registry profile exists, has config, has no profile-local
  `openai-codex` auth shadow, and passes a live provider/model probe. Newly
  created profiles must not be made by cloning `.env` or profile-local auth.

## Incompatible Signs

- Overkill symbols missing after patch.
- `ready` accepts product-facing cards without `product_face_packet`.
- `done` accepts cards without Receipt Five and transition event.
- Security-sensitive cards close without `security_scan_result`.
- vFinal R3/R4 or security-sensitive cards enter material execution without
  `security_architecture_plan`.
- vFinal material execution starts without ready `access_capability` and
  `autonomy_readiness_packet`.
- Executor and reviewer can be the same identity.
- Blocked transition returns exit code `0`.
- Dashboard/API can bypass CLI/Kanban gate behavior.
- Dashboard/API can hard-delete vFinal parent cards or worker subtasks.
- Dashboard/API can manually edit dependency links that touch vFinal parent
  cards or worker subtasks.
- Dashboard/API can delete attachment paths outside the board attachment root.
- Dashboard/API can archive vFinal parent cards or worker subtasks through bulk
  actions.
- Dashboard/API can reassign vFinal parent cards or worker subtasks manually.
- Dashboard/API can reclaim or terminate vFinal worker subtasks through generic
  recovery controls.
- Dashboard/API can specify/rewrite vFinal parent cards or worker subtasks
  through the generic auxiliary specifier route.
- Dashboard/API can decompose vFinal parent cards or worker subtasks through
  the generic auxiliary decomposition route.
- Dashboard/API comments alter task contract fields, status, assignee or
  dependency links instead of appending only comment/event rows.
- Dashboard/API home-subscribe changes task contract fields, status, assignee
  or dependency links instead of only adding/removing notification rows.
- Dashboard/API can archive or hard-delete a board containing vFinal parent
  cards or worker subtasks through generic board controls.
- Dashboard/API board create, metadata patch or switch changes existing vFinal
  task rows, worker subtasks or dependency links.
- Dashboard/API profile patch or auto-description changes existing vFinal task
  rows, worker subtasks or dependency links.
- Dashboard/API orchestration settings change existing vFinal task rows,
  worker subtasks or dependency links.
- Worker subtasks materialize directly as `ready` before worker-route parity and
  worker-route readiness are proven.
- Worker subtasks are not linked as prerequisites of the parent card.
- The parent Factory card can spawn before required worker subtasks finish.
- A real Hermes update is attempted while the production update preflight is
  still `BLOCKED`.

## Required Local Checks

The first check now validates both adapter markers and the installed-runtime
receipt bundle. Required proof receipts must be `PASS`, required safety-block
receipts must be `BLOCKED`, dashboard route inventory must stay at 0 pending
mutating route families, and any unexpected `FAIL` or blocked receipt blocks
the update. It also verifies that the current production update preflight
receipt remains `BLOCKED` with the remaining required production blockers
present until their real proof refs are produced. Finally, it verifies that the sanitized real
Hermes no-spawn control-plane smoke receipt remains `PASS`, that the bounded
real worker-dispatch smoke receipt remains `BLOCKED` with spawn, heartbeat and
cleanup proven, and that the explicit terminal-completion smoke is accepted as
`PASS` only when profile-level live auth, `kanban_complete`, terminal state and
cleanup are all proven. It also verifies that the worker-profile live-auth
matrix receipt remains `PASS` with 46/46 non-human profile probes passing, 20
missing profiles created safely, zero missing profiles after repair and no
profile-local `openai-codex` auth shadow in the registry. Finally, it verifies
that the real local-tool worker smoke remains a bounded `PASS` for
`public-safety-gate` terminal-tool use, structured metadata, `kanban_complete`
closure and explicit non-production limits.

```bash
python adapters/hermes/compatibility-check.py
python adapters/hermes/vfinal-smoke.py
python adapters/hermes/disposable_runtime_smoke.py
python adapters/hermes/validate_v016_transition_patch.py --source-kanban-db /path/to/hermes_cli/kanban_db.py
python adapters/hermes/worker_route_readiness.py --ledger validation/hermes-disposable-runtime/worker-ledger.json --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/worker_profile_readiness_smoke.py --ledger validation/hermes-disposable-runtime/worker-ledger.json --hermes-home /path/to/disposable/hermes/home --overwrite
python adapters/hermes/worker_dispatch_completion_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/worker_real_process_local_stub_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/worker_real_process_matrix_local_stub_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_create_route_parity_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_dispatch_route_parity_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_delete_route_guard_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_links_route_guard_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_attachment_route_safety_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_bulk_archive_guard_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_reassign_route_guard_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_reclaim_terminate_guard_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_specify_route_guard_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_decompose_route_guard_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_comments_route_append_only_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_home_subscribe_route_visibility_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_board_delete_route_guard_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_board_lifecycle_operational_safety_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/dashboard_done_route_parity_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home
python adapters/hermes/service_rollback_drill_smoke.py --hermes-checkout /path/to/disposable/hermes/checkout --hermes-home /path/to/disposable/hermes/home --baseline-tree /path/to/disposable/clean/hermes/tree
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/public_safety_scan.py
```

## Required Hermes Checkout Checks

For the vFinal Hermes v0.16 candidate, run these on a clean Hermes checkout:

```bash
git apply /path/to/0002-add-overkill-vfinal-kanban-transition-hook.patch
git apply /path/to/0003-materialize-overkill-vfinal-worker-subtasks.patch
git apply /path/to/0005-ingest-overkill-worker-results-from-subtasks.patch
git apply /path/to/0006-fix-overkill-worker-subtask-dependency-direction.patch
git apply /path/to/0004-guard-overkill-vfinal-dashboard-ready-route.patch
git apply /path/to/0007-add-dashboard-python-multipart-web-extra.patch
git apply /path/to/0008-guard-overkill-vfinal-dashboard-delete-route.patch
git apply /path/to/0009-guard-overkill-vfinal-dashboard-links-route.patch
git apply /path/to/0010-guard-overkill-vfinal-dashboard-attachment-delete-route.patch
git apply /path/to/0011-guard-overkill-vfinal-dashboard-bulk-archive-route.patch
git apply /path/to/0012-guard-overkill-vfinal-dashboard-reassign-route.patch
git apply /path/to/0013-guard-overkill-vfinal-dashboard-reclaim-terminate-routes.patch
git apply /path/to/0014-guard-overkill-vfinal-dashboard-specify-route.patch
git apply /path/to/0015-guard-overkill-vfinal-dashboard-decompose-route.patch
git apply /path/to/0016-guard-overkill-vfinal-dashboard-board-delete-route.patch
python -m py_compile hermes_cli/kanban_db.py
python -m py_compile plugins/kanban/dashboard/plugin_api.py
```

Then enable the vFinal gate only in the disposable runtime:

```bash
export OVERKILL_FACTORY_KANBAN_GATE=1
export OVERKILL_FACTORY_ADAPTER_ROOT=/path/to/overkill-factory
export OVERKILL_FACTORY_CREATE_WORKER_TASKS=1
export OVERKILL_FACTORY_WORKER_TASK_STATUS=blocked
```

Apply patches only from a real disposable checkout root or a temp tree with its
own `.git` directory. A tree nested inside another repository can make
`git apply` report against the parent repository instead of the intended Hermes
tree.

## Update Receipt

Every update must produce `update-receipt.template.json` filled with:

- before version;
- after version;
- patch apply result;
- compatibility check result;
- disposable adapter runtime smoke result;
- disposable installed-Hermes runtime smoke result;
- disposable worker-subtask materialization smoke result;
- disposable worker-subtask idempotency smoke result;
- disposable worker real-process auth-block smoke result;
- worker-route readiness result;
- worker profile readiness local-stub result;
- worker dispatch completion synthetic result;
- worker real-process local-stub completion result;
- worker real-process matrix local-stub completion result;
- dashboard create-route parity result;
- dashboard dispatch-route parity result;
- dashboard delete-route guard result;
- dashboard links-route guard result;
- dashboard attachment-route safety result;
- dashboard bulk-archive guard result;
- dashboard reassign-route guard result;
- dashboard reclaim/terminate guard result;
- dashboard specify-route guard result;
- dashboard decompose-route guard result;
- dashboard comments append-only result;
- dashboard home-subscribe visibility result;
- dashboard board archive/delete guard result;
- dashboard board lifecycle operational-safety result;
- dashboard profile routes operational-safety result;
- dashboard orchestration route operational-safety result;
- dashboard done-route parity result;
- dashboard route inventory result with 0 pending mutating route families;
- installed-runtime receipt bundle expected-result check;
- production update preflight result;
- production update preflight current blocked-state compatibility check;
- real Hermes no-spawn control-plane smoke result;
- service rollback drill result;
- real Hermes gateway rollback/monitoring smoke result;
- vFinal smoke result;
- real-runtime decision;
- rollback plan.
