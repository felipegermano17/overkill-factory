# Hermes vFinal Production Readiness Status

This is a public-safe readiness status for the vFinal Hermes adapter.

It records what is proven, what is partially proven, and what still blocks a
real Hermes runtime update.

## Verdict

Not production-ready yet.

The adapter has strong disposable-runtime evidence for gates, worker
materialization, dependency direction, dashboard `ready` parity, worker-result
ingestion, safe auth-block failure handling, worker-route readiness blocking and
local-stub worker profile readiness. It also has a synthetic dispatcher
completion proof and a real-process local-stub proof that joins real dispatcher
spawn, Hermes child process execution, `kanban_complete` tool call and parent
ingestion in one disposable path. The matrix smoke repeats the same path for
all 23 vFinal workers in the disposable runtime. The service rollback drill
proves disposable rollback-by-release-restore choreography. Dashboard/API
`POST /tasks` create parity, `POST /dispatch` mechanics,
`DELETE /tasks/{task_id}` hard-delete protection, dependency-link protection,
attachment path safety, bulk-archive protection, reassign protection,
reclaim/terminate protection, specify protection, decompose protection,
comments append-only parity, home-subscribe visibility parity, board
archive/delete protection, board lifecycle operational safety, profile route
operational safety, orchestration route operational safety and `done` parity are also proven after patch `0007` adds the missing
`python-multipart` web dependency. A route inventory now maps the inspected dashboard/API parity surface into
explicit route families. The compatibility check now also verifies the required
installed-runtime receipt bundle, so expected proofs must stay `PASS`, expected
safety blocks must stay `BLOCKED`, and unexpected failed or blocked receipts
stop the update. A separate production update preflight now records the real
runtime decision as `BLOCKED` until the remaining production-only proofs exist.
A real Hermes control-plane no-spawn smoke now proves a disposable board/task
can be created, blocked, read back and archived without dispatching a worker.
A bounded real-worker dispatch smoke now proves the dispatcher can spawn one
worker, create a run record and observe heartbeat on the real runtime, but it is
intentionally recorded as `BLOCKED` because the worker did not complete or block
itself through the expected worker path inside the bounded window.
The follow-up terminal-completion smoke studied the official Hermes docs and
implementation first, then gave the worker an explicit `kanban_complete`
instruction. The first run found a real auth blocker: status output said auth
existed, but the worker profile could not make a live provider request. After
refreshing OpenAI Codex auth at the global Hermes home and removing the stale
local auth shadow from the `factory-orchestrator` profile, the profile-level
provider probe passed and the worker completed through `kanban_complete`.

The profile-wide follow-up then created the 20 missing vFinal worker profiles
from the public worker registry without cloning `.env` or profile-local auth,
verified that all 47 registry profiles now exist, verified that zero registry
profiles retain a local `openai-codex` auth shadow, and ran a live
provider/model probe through all 46 non-human profiles. All 46 passed. The
human gate clerk is intentionally not treated as an autonomous model worker.

A first real local-tool worker smoke then dispatched `public-safety-gate` on a
disposable real Hermes board. The worker used the real terminal tool in a real
workspace, ran read-only checks, returned structured metadata, completed
through `kanban_complete`, and the disposable board was archived. This is a
useful tool-loop checkpoint, and it now backs the `real_tool_auth` production
proof for the local Hermes terminal-tool path. It is not proof of external
SaaS, Discord, cloud, scanner credentials or broad worker-specific tool
authorization.

The same worker result was sanitized into a valid `public_safety_result`, then
used by the parent `done` transition hook. The hook returned `allow_done`, so
`real_worker_done_reconciliation` is now proven for the production preflight.

Scanner-backed specialist output quality is now proven for the bounded
`public-safety-gate` path: the worker ran both public scanners in a disposable
public-safe workspace, produced a structured `public_safety_result`, completed
through `kanban_complete`, and the board/workspace were cleaned up.

Production rollback/monitoring is now proven for the real Hermes gateway path:
the systemd unit was checked while healthy, the gateway process was terminated
under controlled conditions, systemd recreated it through `Restart=always`, and
post-recovery Hermes status plus Kanban health checks passed.

The remaining production blockers are Operator Control Tower proof and a
passing complete update receipt. A blocked update receipt already exists to
record the current state and point at the missing Control Tower proof.
The Control Tower production harness now records the exact missing pieces:
real Discord mapping, runtime registration event and bridge health evidence
that follows `schemas/operator-control-tower-bridge-health.schema.json`.

## Proven

| Area | Status | Evidence |
| --- | --- | --- |
| Patch apply and compile for `kanban_db.py` | PASS | `validation/hermes-v016-transition-patch/patch-apply-receipt.json` |
| Patch apply and compile for dashboard/API `plugin_api.py` | PASS | `validation/hermes-v016-transition-patch/dashboard-route-patch-apply-receipt.json` |
| Direct `ready` creation blocks weak vFinal cards | PASS | `validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json` |
| Complete vFinal cards can enter `ready` | PASS | `validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json` |
| Weak `done` is blocked without Receipt Five/worker evidence | PASS | `validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json` |
| Valid `done` can pass with Receipt Five and worker results | PASS | `validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json` |
| Manual unblock-to-ready rechecks the gate | PASS | `validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json` |
| Automatic recompute-to-ready rechecks the gate | PASS | `validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json` |
| Worker ledger materializes as real Hermes subtasks | PASS | `validation/hermes-installed-runtime-smoke/worker-subtasks-smoke.json` |
| Worker materialization is idempotent on CLI retry | PASS | `validation/hermes-installed-runtime-smoke/worker-subtasks-idempotency-smoke.json` |
| Dashboard/API `status=ready` cannot bypass the gate | PASS | `validation/hermes-installed-runtime-smoke/dashboard-route-parity-smoke.json` |
| Dashboard dependency patch adds `python-multipart` to Hermes `web` extra | PASS | `validation/hermes-v016-transition-patch/dashboard-dependency-patch-apply-receipt.json` |
| Dashboard/API `POST /tasks` cannot bypass before-ready creation | PASS | `validation/hermes-installed-runtime-smoke/dashboard-create-route-parity-smoke.json` |
| Dashboard/API `POST /dispatch` respects dispatcher mechanics | PASS | `validation/hermes-installed-runtime-smoke/dashboard-dispatch-route-parity-smoke.json` |
| Dashboard/API `DELETE /tasks/{task_id}` blocks vFinal hard-delete | PASS | `validation/hermes-installed-runtime-smoke/dashboard-delete-route-guard-smoke.json` |
| Dashboard/API `POST /links` and `DELETE /links` protect vFinal dependencies | PASS | `validation/hermes-installed-runtime-smoke/dashboard-links-route-guard-smoke.json` |
| Dashboard/API attachment upload/delete paths are guarded | PASS | `validation/hermes-installed-runtime-smoke/dashboard-attachment-route-safety-smoke.json` |
| Dashboard/API bulk archive blocks vFinal parent/workers | PASS | `validation/hermes-installed-runtime-smoke/dashboard-bulk-archive-guard-smoke.json` |
| Dashboard/API reassign blocks vFinal parent/workers | PASS | `validation/hermes-installed-runtime-smoke/dashboard-reassign-route-guard-smoke.json` |
| Dashboard/API reclaim/terminate blocks generic recovery for vFinal workers | PASS | `validation/hermes-installed-runtime-smoke/dashboard-reclaim-terminate-guard-smoke.json` |
| Dashboard/API specify blocks generic auxiliary rewrite/promotion for vFinal parent/workers | PASS | `validation/hermes-installed-runtime-smoke/dashboard-specify-route-guard-smoke.json` |
| Dashboard/API decompose blocks generic auxiliary task-graph fan-out for vFinal parent/workers | PASS | `validation/hermes-installed-runtime-smoke/dashboard-decompose-route-guard-smoke.json` |
| Dashboard/API comments append only operator notes without task contract changes | PASS | `validation/hermes-installed-runtime-smoke/dashboard-comments-route-append-only-smoke.json` |
| Dashboard/API home-subscribe toggles only notification visibility rows | PASS | `validation/hermes-installed-runtime-smoke/dashboard-home-subscribe-route-visibility-smoke.json` |
| Dashboard/API board archive/delete blocks boards containing vFinal work | PASS | `validation/hermes-installed-runtime-smoke/dashboard-board-delete-route-guard-smoke.json` |
| Dashboard/API board create/patch/switch only affects board metadata/current selection | PASS | `validation/hermes-installed-runtime-smoke/dashboard-board-lifecycle-operational-safety-smoke.json` |
| Dashboard/API profile patch/auto-describe only affects profile metadata | PASS | `validation/hermes-installed-runtime-smoke/dashboard-profile-routes-operational-safety-smoke.json` |
| Dashboard/API orchestration settings only affect Kanban config knobs | PASS | `validation/hermes-installed-runtime-smoke/dashboard-orchestration-route-operational-safety-smoke.json` |
| Dashboard/API `status=done` and bulk `status=done` respect the before-done gate | PASS | `validation/hermes-installed-runtime-smoke/dashboard-done-route-parity-smoke.json` |
| Dashboard/API route inventory maps remaining parity surface | PASS | `validation/hermes-installed-runtime-smoke/dashboard-route-inventory-smoke.json` |
| Installed-runtime receipt bundle has expected PASS/BLOCKED results | PASS | `adapters/hermes/compatibility-check.py` |
| Real-runtime update preflight blocks missing production-only proofs | PASS | `validation/hermes-production-update-preflight/real-runtime-update-blocked.json` |
| Real Hermes no-spawn control-plane smoke passes on a disposable board | PASS | `validation/hermes-real-runtime-smoke/no-spawn-blocked-board-smoke.json` |
| All non-human vFinal worker profiles can use live OpenAI Codex model auth | PASS | `validation/hermes-real-runtime-smoke/worker-profile-live-auth-matrix-smoke.json` |
| Real Hermes local terminal tool authorization is proven for one bounded worker | PASS | `validation/hermes-production-proof/real-tool-auth.json` |
| Real Hermes scanner-backed specialist quality is proven for one bounded worker | PASS | `validation/hermes-production-proof/specialist-output-quality.json` |
| Parent `done` reconciliation passes with a real worker result | PASS | `validation/hermes-production-proof/real-worker-done-reconciliation.json` |
| Real Hermes gateway rollback/monitoring recovery is proven | PASS | `validation/hermes-production-proof/production-rollback-monitoring.json` |
| Completed worker subtasks can write parent worker-result artifacts | PASS | `validation/hermes-installed-runtime-smoke/worker-result-ingestion-smoke.json` |
| Parent `done` can find auto-ingested worker-result artifacts | PASS | `validation/hermes-installed-runtime-smoke/worker-result-ingestion-smoke.json` |
| Worker subtasks are prerequisites of the parent card | PASS | `validation/hermes-installed-runtime-smoke/worker-dispatch-route-smoke.json` |
| Spawnable materialized workers can be claimed by dispatcher | PASS | `validation/hermes-installed-runtime-smoke/worker-dispatch-route-smoke.json` |
| Default dispatcher spawn path can start a real Hermes worker process | PASS | `validation/hermes-installed-runtime-smoke/worker-real-process-auth-block-smoke.json` |
| Missing provider/model blocks safely instead of pretending success | PASS | `validation/hermes-installed-runtime-smoke/worker-real-process-auth-block-smoke.json` |
| Worker-route readiness blocks unsafe production dispatch | PASS | `validation/hermes-installed-runtime-smoke/worker-route-readiness-blocked.json` |
| Disposable worker profiles can be provisioned against a local OpenAI-compatible stub | PASS | `validation/hermes-installed-runtime-smoke/worker-profile-readiness-local-stub-smoke.json` |
| Dispatcher can claim a materialized worker and ingest a synthetic completion | PASS | `validation/hermes-installed-runtime-smoke/worker-dispatch-completion-smoke.json` |
| Real Hermes child process can call `kanban_complete` through a local OpenAI-compatible streaming stub | PASS | `validation/hermes-installed-runtime-smoke/worker-real-process-local-stub-smoke.json` |
| All 23 vFinal worker routes can complete through real Hermes child processes against a local streaming stub | PASS | `validation/hermes-installed-runtime-smoke/worker-real-process-matrix-local-stub-smoke.json` |
| Disposable rollback-by-release-restore drill restores baseline, passes health checks, restarts a service-like probe and restores patched state | PASS | `validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json` |

## Partially Proven

| Area | What Is Proven | What Is Not Proven |
| --- | --- | --- |
| Worker execution | Dispatcher can claim workers; `_default_spawn` starts a real process; all 23 provisioned profiles can complete through a local streaming stub; one real non-stub worker completed through live OpenAI Codex. | Broad specialist quality across the worker registry is not proven. |
| Real Hermes worker dispatch | A bounded disposable-board smoke spawned one real worker process, created a run record, observed heartbeat, reclaimed/blocked the task after timeout, archived the board and verified process cleanup. | By itself, this older smoke did not prove completion or quality; later receipts cover completion and local terminal tool auth. |
| Real Hermes terminal completion | Official Hermes docs and implementation were studied, the worker profile had the Kanban worker skill, global and profile-level live provider probes passed, a disposable task explicitly instructed `kanban_complete`, and the worker reached `done` through `kanban_complete`. | This still does not prove broad specialist output quality or production rollback. |
| Real Hermes profile auth matrix | All 47 vFinal registry profiles now exist. The 46 non-human profiles passed a live `openai-codex` + `gpt-5.5` provider/model probe. The 20 missing profiles were created without cloning `.env` or profile-local auth. | This still does not prove external SaaS/cloud/browser credentials, specialist output quality, Control Tower readiness or production rollback. |
| Real Hermes local tool worker smoke | A disposable `public-safety-gate` task used the real terminal tool in a real workspace, ran read-only checks, produced structured metadata and completed through `kanban_complete`. | This proves local terminal tool authorization for one bounded worker; it does not prove external SaaS tools, Discord, cloud, scanner credentials or broad worker quality. |
| Real worker parent reconciliation | A sanitized real `public_safety_result` from the real worker satisfied the parent `done` hook; the hook returned `allow_done`. | This does not prove production rollout readiness. |
| Specialist output quality | A stronger public-safety specialist smoke ran the public safety and secret safety scanners through a real Hermes worker and completed with structured metadata. | This is bounded to the `public-safety-gate` scanner path; future specialist/tool paths still need card-specific evidence. |
| Worker completion wiring | One materialized worker subtask can be claimed, completed with synthetic metadata, completed by a real child process through `kanban_complete`, ingested by the parent card, and reconciled from a sanitized real worker result. | Broad autonomous specialist output quality is not proven. |
| Worker-route readiness | The first receipt proves 23/23 routes block when profile/config/model/provider readiness is missing. The local-stub receipt proves all 23 disposable profiles can pass shape and `/models` checks. | Broad specialist output quality and non-terminal external tool auth remain card-specific. |
| Worker result ingestion | Synthetic structured metadata from completed subtasks is ingested, and a real worker-produced `public_safety_result` can satisfy before-done reconciliation. | Production scanner-backed specialist quality is not proven yet. |
| Dashboard/API parity | `POST /tasks`, attachment upload/delete, `POST /dispatch`, `DELETE /tasks/{task_id}`, `POST /links`, `DELETE /links`, `POST /tasks/{task_id}/reassign`, `POST /tasks/{task_id}/reclaim`, `POST /runs/{run_id}/terminate`, `POST /tasks/{task_id}/specify`, `POST /tasks/{task_id}/decompose`, `POST /tasks/{task_id}/comments`, `POST /tasks/{task_id}/home-subscribe/{platform}`, `DELETE /tasks/{task_id}/home-subscribe/{platform}`, `POST /boards`, `PATCH /boards/{slug}`, `DELETE /boards/{slug}`, `POST /boards/{slug}/switch`, `PATCH /profiles/{profile_name}`, `POST /profiles/{profile_name}/describe-auto`, `PUT /orchestration`, `status=ready`, bulk `status=ready`, `status=done`, bulk `status=done` and bulk `archive=True` are gated, guarded, append-only, visibility-only, metadata-only, current-pointer-only, config-only or dispatcher-mechanics proven. Patch `0007` fixes the dashboard plugin import dependency for FastAPI `File/Form` routes. The route inventory maps 41 routes, 24 mutating routes, 24 covered mutating route families and 0 pending mutating route families; `compatibility-check.py` now enforces that zero-pending state and the expected installed-runtime receipt bundle results. | Future dashboard/API route additions still need inventory and proof before real runtime update. Worker routes still need production-quality proof. |
| Rollback | Patch reversal compiled and removed markers in disposable runtime. A disposable rollback-by-release-restore drill restored clean baseline files, passed health checks, restarted a service-like probe and restored patched adapter state. The real gateway also recovered through systemd `Restart=always` and passed Hermes/Kanban health checks. | Code-version rollback, package rollback, Discord recovery, cloud rollback and external monitoring still belong in the complete update receipt and production operations plan. |
| Real-runtime update preflight | The factory now has an executable preflight that blocks a real Hermes update when production-only proofs are missing. | It is currently `BLOCKED`: `non_stub_worker_execution`, `real_tool_auth`, `specialist_output_quality`, `real_worker_done_reconciliation` and `production_rollback_monitoring` are `PASS`; `operator_control_tower` is missing and `complete_update_receipt` points at a blocked receipt. |
| Real Hermes control-plane smoke | A disposable board and unassigned task can be created, blocked, read back with a blocked event/run record, and archived through recoverable cleanup. | This does not prove worker dispatch, non-stub model execution, tool auth, specialist quality, dashboard parity, release readiness or production rollback. |

## Blocking Items Before Real Runtime Update

1. Require each worker to complete through `kanban_complete` or block through
   `kanban_block`; no conversational exit is acceptable.
2. Keep dashboard/API route inventory at 0 pending mutating families before any
   real runtime update; any future route addition needs explicit parity or
   operational-safety proof. Remaining worker-route parity still needs
   production-quality proof beyond local-stub receipts.
3. Produce the operator control tower proof before using the factory in
   production.
4. Turn the blocked update receipt into a passing complete update receipt
   before touching any real Hermes runtime. That receipt must include
   package/code rollback, monitoring owner,
   post-update success check and rollback trigger.
5. Re-run `adapters/hermes/production_update_preflight.py` with proof refs and
    require `PASS` before touching any real Hermes runtime.

## Production Rule

Do not set `OVERKILL_FACTORY_WORKER_TASK_STATUS=ready` in production until the
blocking items above pass in a disposable runtime.

Until then, materialized worker subtasks should remain `blocked` by default.

The worker-route readiness receipts are now the hard preflight for this rule:

```text
validation/hermes-installed-runtime-smoke/worker-route-readiness-blocked.json
validation/hermes-installed-runtime-smoke/worker-profile-readiness-local-stub-smoke.json
validation/hermes-installed-runtime-smoke/worker-dispatch-completion-smoke.json
validation/hermes-installed-runtime-smoke/worker-real-process-local-stub-smoke.json
validation/hermes-installed-runtime-smoke/worker-real-process-matrix-local-stub-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-reclaim-terminate-guard-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-specify-route-guard-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-decompose-route-guard-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-comments-route-append-only-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-home-subscribe-route-visibility-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-board-delete-route-guard-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-board-lifecycle-operational-safety-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-profile-routes-operational-safety-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-orchestration-route-operational-safety-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-done-route-parity-smoke.json
validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json
validation/hermes-production-update-preflight/real-runtime-update-blocked.json
validation/hermes-real-runtime-smoke/no-spawn-blocked-board-smoke.json
validation/hermes-real-runtime-smoke/real-worker-dispatch-bounded-smoke.json
validation/hermes-real-runtime-smoke/real-worker-terminal-completion-smoke.json
validation/hermes-real-runtime-smoke/worker-profile-live-auth-matrix-smoke.json
validation/hermes-real-runtime-smoke/real-worker-local-tool-quality-smoke.json
validation/hermes-real-runtime-smoke/production-rollback-monitoring-smoke.json
validation/control-tower/operator-control-tower-production-readiness.json
validation/hermes-production-update-preflight/current-update-receipt-blocked.json
```

The local-stub receipts may unblock the next disposable smoke. They do not
authorize production `ready` workers by themselves.

The bounded real-worker dispatch receipt is also not an authorization receipt.
It is a useful diagnostic checkpoint: spawn, run record, heartbeat and cleanup
worked; autonomous terminal completion did not.

The terminal-completion receipt closes the single-profile auth/completion
blocker for `factory-orchestrator`. The worker-profile live-auth matrix receipt
closes profile-level model auth for every non-human vFinal worker profile.
The remaining production proofs are the operator-facing Control Tower and the
complete update receipt; future external tools remain card-specific proof
obligations.
