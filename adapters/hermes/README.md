# Hermes Adapter

Hermes is the first-class runtime for Overkill Factory.

The adapter hardens Hermes Kanban so Factory cards cannot move through the
production line unless their contracts are complete.

## Patch

```text
patches/0001-add-overkill-factory-10-kanban-gates.patch
patches/0002-add-overkill-vfinal-kanban-transition-hook.patch
patches/0003-materialize-overkill-vfinal-worker-subtasks.patch
patches/0004-guard-overkill-vfinal-dashboard-ready-route.patch
patches/0005-ingest-overkill-worker-results-from-subtasks.patch
patches/0006-fix-overkill-worker-subtask-dependency-direction.patch
patches/0007-add-dashboard-python-multipart-web-extra.patch
patches/0008-guard-overkill-vfinal-dashboard-delete-route.patch
patches/0009-guard-overkill-vfinal-dashboard-links-route.patch
patches/0010-guard-overkill-vfinal-dashboard-attachment-delete-route.patch
patches/0011-guard-overkill-vfinal-dashboard-bulk-archive-route.patch
patches/0012-guard-overkill-vfinal-dashboard-reassign-route.patch
patches/0013-guard-overkill-vfinal-dashboard-reclaim-terminate-routes.patch
patches/0014-guard-overkill-vfinal-dashboard-specify-route.patch
patches/0015-guard-overkill-vfinal-dashboard-decompose-route.patch
patches/0016-guard-overkill-vfinal-dashboard-board-delete-route.patch
```

The first patch adds:

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
- Regression tests.

This is the legacy Factory 10 patch.

The second patch is an opt-in Hermes v0.16 candidate for vFinal. It calls the
Kanban task JSON bridge before direct `ready` creation, automatic ready
recompute, manual `promote_task`, `unblock_task` to `ready` and `complete_task`
transitions, records allow/block events and blocks weak Factory cards before
`ready` or `done`.

The third patch is also opt-in. It turns the worker ledger produced by the
vFinal gate into real Hermes worker subtasks linked to the parent card. By
default those subtasks are born `blocked`; this is intentional no-spawn safety
until worker-route parity has been proven.

The fourth patch guards the dashboard/API `status=ready` path. It routes
Overkill vFinal cards through the same gated `promote_task`/`unblock_task`
logic instead of letting dashboard drag/drop or bulk update write `ready`
directly.

The fifth patch ingests completed worker subtasks back into the parent card's
runtime evidence area. A completed Overkill worker subtask can write a
worker-result JSON artifact, emit child and parent ingestion events, and let
parent `done` reconciliation find those artifacts automatically.

The sixth patch fixes the worker dependency direction. Worker subtasks are
prerequisites of the parent Factory card, so the workers can dispatch first and
the parent card waits for their evidence instead of blocking the workers behind
the parent.

For the current vFinal Hermes v0.16 validation path, apply `0002` and then
`0003`, then `0005`, then `0006` to a clean Hermes v0.16 `kanban_db.py`, and
apply `0004`, `0008`, `0009`, `0010`, `0011`, `0012`, `0013`, `0014`, `0015`
and `0016` to the clean
Hermes v0.16 `plugins/kanban/dashboard/plugin_api.py`. Apply `0007` to the
checkout dependency files before dashboard smokes. Do not assume `0001` applies
first unless a combined Factory 10 + vFinal port has been explicitly proven.

It requires:

```text
OVERKILL_FACTORY_KANBAN_GATE=1
OVERKILL_FACTORY_ADAPTER_ROOT=/path/to/overkill-factory
OVERKILL_FACTORY_CREATE_WORKER_TASKS=1
OVERKILL_FACTORY_WORKER_TASK_STATUS=blocked
```

Patch-level validation:

```text
python adapters/hermes/validate_v016_transition_patch.py --source-kanban-db /path/to/hermes_cli/kanban_db.py
python adapters/hermes/validate_v016_dashboard_route_patch.py --source-plugin-api /path/to/plugins/kanban/dashboard/plugin_api.py
validation/hermes-v016-transition-patch/patch-apply-receipt.json
validation/hermes-v016-transition-patch/dashboard-route-patch-apply-receipt.json
```

This proves patch apply and compile only. Disposable installed-Hermes CLI/Kanban
evidence is recorded separately under:

```text
validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json
validation/hermes-installed-runtime-smoke/worker-subtasks-smoke.json
validation/hermes-installed-runtime-smoke/worker-subtasks-idempotency-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-route-parity-smoke.json
validation/hermes-installed-runtime-smoke/worker-result-ingestion-smoke.json
validation/hermes-installed-runtime-smoke/worker-dispatch-route-smoke.json
validation/hermes-installed-runtime-smoke/worker-real-process-auth-block-smoke.json
validation/hermes-installed-runtime-smoke/worker-route-readiness-blocked.json
validation/hermes-installed-runtime-smoke/worker-profile-readiness-local-stub-smoke.json
validation/hermes-installed-runtime-smoke/worker-dispatch-completion-smoke.json
validation/hermes-installed-runtime-smoke/worker-real-process-local-stub-smoke.json
validation/hermes-installed-runtime-smoke/worker-real-process-matrix-local-stub-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-create-route-parity-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-dispatch-route-parity-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-delete-route-guard-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-links-route-guard-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-attachment-route-safety-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-bulk-archive-guard-smoke.json
validation/hermes-installed-runtime-smoke/dashboard-reassign-route-guard-smoke.json
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
validation/hermes-real-runtime-smoke/worker-profile-live-auth-matrix-smoke.json
validation/hermes-real-runtime-smoke/real-worker-local-tool-quality-smoke.json
validation/hermes-real-runtime-smoke/production-rollback-monitoring-smoke.json
```

Production readiness still requires Operator Control Tower proof and a passing
complete update receipt. A blocked update receipt now records the current
state. Local terminal-tool auth, scanner-backed specialist output quality,
parent `done` reconciliation and real gateway rollback/monitoring recovery are
now proven for bounded real worker results.
The Operator Control Tower production harness records the exact remaining
private inputs: real Discord mapping, runtime registration event and bridge
health evidence. The bridge health input must follow
`schemas/operator-control-tower-bridge-health.schema.json`; a generic passing
JSON is not a production proof.
Do not set `OVERKILL_FACTORY_WORKER_TASK_STATUS=ready` in production until real
tool use and result quality are proven. Run
`adapters/hermes/worker_route_readiness.py` against the worker ledger and target
Hermes home first; a `BLOCKED` receipt means worker subtasks must remain born
`blocked`. The local-stub profile readiness smoke is useful evidence for
profile/config/model/provider shape, but it is not real model or tool proof.
The real worker-profile live-auth matrix proves that every non-human vFinal
worker profile can answer through the live `openai-codex` + `gpt-5.5` path, and
also records that the 20 newly required profiles were created without cloning
`.env` or profile-local auth.
The real local-tool worker smoke proves one `public-safety-gate` worker can use
the real Hermes terminal tool in a real workspace, perform read-only checks,
return structured metadata and complete through `kanban_complete`. It is not a
claim that external SaaS, Discord, cloud or scanner credentials are ready.
The real parent-reconciliation smoke proves that a sanitized real
`public_safety_result` can satisfy the before-done hook and return
`allow_done`. The specialist-quality smoke proves the real worker can run the
public safety and secret safety scanners in a disposable public-safe workspace
and return scanner-backed structured metadata.
The synthetic dispatch-completion smoke is useful evidence for dispatcher,
completion and ingestion wiring, but it is not autonomous specialist proof.
The real-process local-stub smoke is stronger: it proves the real dispatcher can
spawn a real Hermes child, expose `kanban_complete`, execute the tool-call loop
and ingest the result into the parent. It is still not real model/tool quality
proof because the model endpoint is deterministic and local.
The real-process matrix local-stub smoke repeats that stronger path for all 23
vFinal worker routes in the disposable runtime.
The dashboard create-route parity smoke proves dashboard/API `POST /tasks` does
not expose a `status` field, blocks weak direct ready creation, and allows valid
direct ready creation with blocked worker subtasks.
The dashboard dispatch-route parity smoke proves dashboard/API `POST /dispatch`
does not spawn blocked worker subtasks, does not spawn the parent Factory card
while worker prerequisites remain open, and can spawn a selected ready worker
through a stubbed spawn function.
The dashboard links-route guard smoke proves dashboard/API `POST /links` and
`DELETE /links` cannot manually edit dependency links that touch vFinal parent
cards or worker subtasks, while ordinary disposable task links still work.
The dashboard attachment-route safety smoke proves dashboard/API
`POST /tasks/{task_id}/attachments` sanitizes traversal filenames under the
board attachment root, ordinary attachment delete works, and
`DELETE /attachments/{attachment_id}` refuses a tampered outside-root path.
The dashboard bulk-archive guard smoke proves dashboard/API `POST /tasks/bulk`
with `archive=True` cannot archive vFinal parent cards or worker subtasks, while
ordinary disposable tasks can still be archived.
The dashboard reassign-route guard smoke proves dashboard/API
`POST /tasks/{task_id}/reassign` cannot manually change the execution profile
of vFinal parent cards or worker subtasks, while ordinary disposable tasks can
still be reassigned.
The dashboard reclaim/terminate guard smoke proves dashboard/API
`POST /tasks/{task_id}/reclaim` and `POST /runs/{run_id}/terminate` cannot
generically abort vFinal worker subtasks, while ordinary disposable task
recovery still works.
The dashboard specify-route guard smoke proves dashboard/API
`POST /tasks/{task_id}/specify` cannot rewrite or promote vFinal parent cards
or worker subtasks through the generic auxiliary specifier route, while
ordinary disposable task specify still works.
The dashboard decompose-route guard smoke proves dashboard/API
`POST /tasks/{task_id}/decompose` cannot create a parallel task graph for
vFinal parent cards or worker subtasks through the generic auxiliary decomposer,
while ordinary disposable task decompose still works.
The dashboard comments append-only smoke proves dashboard/API
`POST /tasks/{task_id}/comments` remains available for vFinal supervision, but
only appends comment/event rows. It does not change task status, body, assignee
or dependency links, and comments are not authoritative gate evidence.
The dashboard home-subscribe visibility smoke proves dashboard/API
`POST /tasks/{task_id}/home-subscribe/{platform}` and
`DELETE /tasks/{task_id}/home-subscribe/{platform}` only add/remove notification
subscription rows for owner visibility. They do not change task status, body,
assignee or dependency links.
The dashboard board-delete guard smoke proves dashboard/API
`DELETE /boards/{slug}` cannot archive or hard-delete a board that contains
vFinal parent cards or worker subtasks, while ordinary disposable boards can
still be archived or deleted. Its receipt redacts local archive paths.
The dashboard board-lifecycle operational-safety smoke proves dashboard/API
`POST /boards`, `PATCH /boards/{slug}` and `POST /boards/{slug}/switch` only
create board metadata, update display metadata or change the current-board
pointer. They do not mutate existing vFinal task graphs, worker subtasks or
dependency links.
The dashboard profile-routes operational-safety smoke proves dashboard/API
`PATCH /profiles/{profile_name}` and
`POST /profiles/{profile_name}/describe-auto` only update profile metadata.
The auto-description success path uses a local stub, so the route is proven
without a real auxiliary model call.
The dashboard orchestration-route operational-safety smoke proves dashboard/API
`PUT /orchestration` only updates Kanban orchestration config knobs. Missing
profiles are rejected before save, valid settings are persisted, overrides can
be cleared, and existing vFinal task graphs are not mutated.
The dashboard done-route parity smoke proves dashboard/API `status=done`
follows the before-done gate: weak `done` is refused, valid `done` is allowed
with Receipt Five and worker-result metadata, and bulk weak `done` is refused.
Patch `0007` adds `python-multipart` to the Hermes `web` extra so the Kanban
dashboard plugin can import when routes use FastAPI `File/Form`.
The service rollback drill proves a rollback-by-release-restore path in the
disposable runtime: restore clean baseline source files, run health checks,
stop/start a service-like process probe, and restore the patched adapter state.
It is not a systemd/Windows service or production monitoring proof.

vFinal support is layered through `scripts/factoryctl.py` and the transition
hook. The public hook now recognizes `OVERKILL_VFINAL` cards, including:

- Product Outcome and Discovery contracts;
- Agentic Method Router;
- Software Development, Product Experience, Data/Metrics and Agent Eval plans;
- Security Architecture before material security-sensitive execution;
- Access and Capability Gate;
- Autonomy Readiness Packet;
- Budget, dependency, production and maturity workers.

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

When Hermes provides a Kanban task JSON payload instead of a direct card file,
use the bridge:

```bash
python adapters/hermes/kanban_event_bridge.py \
  --task-json path/to/hermes-task.json \
  --from-status blocked \
  --to-status ready \
  --ledger path/to/worker-ledger.json \
  --out path/to/hook-result.json
```

The bridge reads the task body as the factory card, calls the same transition
hook, and records the transition decision. Patch `0003` can materialize the
resulting worker ledger as real Hermes subtasks; the bridge itself is still an
adapter edge, not a runtime dispatcher.

Installed Hermes integration must happen at the Kanban transition decision
point, not as a shell hook around unrelated agent/tool events. See
`adapters/hermes/kanban-transition-hook-integration.md`.

Current automation is intentionally an orchestration and reconciliation layer.
It does not replace real Codex Security scans, solanabr/Auditor runs,
screenshots, independent reviews, or human approval records.

For vFinal, the hook must also block material execution when required security
architecture, access readiness or autonomy readiness evidence is missing.

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

vFinal smoke evidence:

- `validation/cards/vfinal-r3-ready.md` routes the new vFinal workers.
- `validation/cards/vfinal-r3-missing-security-access.md` blocks missing
  security architecture, access readiness and autonomy readiness.
- `validation/cards/vfinal-control-tower-missing-interface.md` proves owner
  interface and Control Tower work cannot become ready without projection,
  event, approval and Discord mapping evidence.
- `validation/hermes-smoke/vfinal-transition-smoke.json` records the local
  transition-hook smoke.
- `validation/hermes-disposable-runtime/disposable-runtime-smoke.json` records a
  repository-local disposable adapter runtime smoke covering before-ready,
  idempotent retry, before-ready blocking, before-done blocking, before-done
  `allow_done`, Kanban task JSON bridge and Control Tower blocking.
- `validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json`
  records a disposable installed-Hermes CLI/Kanban smoke covering direct
  `ready` creation blocking, positive `ready` allowance with worker ledger
  creation, weak `done` blocking, positive `done` allowance with Receipt Five
  plus worker results, manual unblock-to-ready blocking and automatic
  recompute-to-ready blocking. It also records patch reversal rollback in the
  disposable runtime.
- `validation/hermes-v016-transition-patch/dashboard-dependency-patch-apply-receipt.json`
  records the `0007` dashboard dependency patch validation for
  `python-multipart` in the Hermes `web` extra.
- `validation/hermes-installed-runtime-smoke/dashboard-create-route-parity-smoke.json`
  records dashboard/API `POST /tasks` create-route parity: no exposed `status`
  field, weak direct ready creation blocked, and valid direct ready creation
  with blocked worker subtasks.
- `validation/hermes-installed-runtime-smoke/dashboard-dispatch-route-parity-smoke.json`
  records dashboard/API `POST /dispatch` mechanics: blocked workers do not
  spawn, the parent Factory card does not spawn while prerequisites are open,
  and one selected ready worker can be spawned with a stubbed spawn function.
- `validation/hermes-installed-runtime-smoke/dashboard-delete-route-guard-smoke.json`
  records dashboard/API `DELETE /tasks/{task_id}` hard-delete protection:
  vFinal parent cards and worker subtasks are blocked from destructive delete,
  worker prerequisite links stay intact, and ordinary disposable non-factory
  tasks can still be deleted.
- `validation/hermes-installed-runtime-smoke/dashboard-links-route-guard-smoke.json`
  records dashboard/API `POST /links` and `DELETE /links` dependency protection:
  manual link edits that touch vFinal parent cards or worker subtasks are
  blocked, while ordinary disposable task links can still be added and removed.
- `validation/hermes-installed-runtime-smoke/dashboard-attachment-route-safety-smoke.json`
  records dashboard/API attachment safety: traversal filenames are sanitized
  under the board attachment root, normal attachment delete works, and tampered
  outside-root delete is blocked.
- `validation/hermes-installed-runtime-smoke/dashboard-bulk-archive-guard-smoke.json`
  records dashboard/API bulk archive protection: vFinal parent cards and worker
  subtasks are blocked from `archive=True`, while ordinary disposable task
  archive still works.
- `validation/hermes-installed-runtime-smoke/dashboard-reassign-route-guard-smoke.json`
  records dashboard/API reassign protection: vFinal parent cards and worker
  subtasks cannot have execution profile changed manually, while ordinary
  disposable task reassign still works.
- `validation/hermes-installed-runtime-smoke/dashboard-reclaim-terminate-guard-smoke.json`
  records dashboard/API reclaim/terminate protection: vFinal worker subtasks
  cannot be aborted through generic recovery controls, while ordinary
  disposable task recovery still works.
- `validation/hermes-installed-runtime-smoke/dashboard-specify-route-guard-smoke.json`
  records dashboard/API specify protection: vFinal parent cards and worker
  subtasks cannot be rewritten or promoted through the generic auxiliary
  specifier route, while ordinary disposable task specify still works.
- `validation/hermes-installed-runtime-smoke/dashboard-decompose-route-guard-smoke.json`
  records dashboard/API decompose protection: vFinal parent cards and worker
  subtasks cannot be fanned out through the generic auxiliary decomposer, while
  ordinary disposable task decompose still works.
- `validation/hermes-installed-runtime-smoke/dashboard-comments-route-append-only-smoke.json`
  records dashboard/API comments parity: comments stay available for operator
  notes but append only comment/event rows and do not alter task contract,
  status, assignee or dependency links.
- `validation/hermes-installed-runtime-smoke/dashboard-home-subscribe-route-visibility-smoke.json`
  records dashboard/API home-subscribe parity: subscription toggles add/remove
  only notification rows for owner visibility and do not alter task contract,
  status, assignee or dependency links.
- `validation/hermes-installed-runtime-smoke/dashboard-board-delete-route-guard-smoke.json`
  records dashboard/API board archive/delete protection: boards containing
  vFinal parent cards or worker subtasks cannot be archived or hard-deleted
  through generic board controls, while ordinary disposable boards still can.
- `validation/hermes-installed-runtime-smoke/dashboard-board-lifecycle-operational-safety-smoke.json`
  records dashboard/API board lifecycle safety: create, metadata patch and
  switch routes do not mutate existing vFinal task graphs, worker subtasks or
  dependency links.
- `validation/hermes-installed-runtime-smoke/dashboard-profile-routes-operational-safety-smoke.json`
  records dashboard/API profile route safety: manual profile descriptions and
  stubbed auto-descriptions update only profile metadata and do not mutate
  vFinal task graphs, worker subtasks or dependency links.
- `validation/hermes-installed-runtime-smoke/dashboard-orchestration-route-operational-safety-smoke.json`
  records dashboard/API orchestration route safety: `PUT /orchestration`
  rejects missing profiles before save, persists valid Kanban orchestration
  knobs, clears overrides and does not mutate vFinal task graphs.
- `validation/hermes-installed-runtime-smoke/dashboard-done-route-parity-smoke.json`
  records dashboard/API `status=done` and bulk `status=done` parity with the
  before-done gate.
- `validation/hermes-installed-runtime-smoke/dashboard-route-inventory-smoke.json`
  records the inspected dashboard/API route surface. The compatibility check
  requires this receipt to stay at 0 pending mutating route families.
- `adapters/hermes/compatibility-check.py` also verifies the required installed
  runtime receipt bundle: proof receipts must remain `PASS`, the worker-route
  safety preflight must remain `BLOCKED`, and no unexpected `FAIL` or blocked
  receipt may appear before a real runtime update.
- `validation/hermes-production-update-preflight/real-runtime-update-blocked.json`
  records the real-runtime update preflight. It is intentionally `BLOCKED`
  until operator control tower readiness and a passing complete update receipt
  are both proven.
- `validation/hermes-production-update-preflight/current-update-receipt-blocked.json`
  records the current public-safe update receipt in blocked state. It preserves
  all passed checks and points at the missing operator Control Tower proof.
- `validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json`
  records a disposable rollback-by-release-restore drill covering clean
  baseline restore, health checks, service-like stop/start and patched-state
  restoration.
- `validation/hermes-real-runtime-smoke/production-rollback-monitoring-smoke.json`
  records a real Hermes gateway recovery proof through systemd `Restart=always`
  plus post-recovery Hermes status and Kanban health checks.
- `validation/remote-proof/vfinal-local-clean-smoke.json` records a clean
  tempdir proof.
- `validation/hermes-smoke/vfinal-local-update-receipt.json` summarizes the
  local adapter result.

## Apply

From a Hermes checkout:

```bash
git switch -c codex/overkill-factory-10-gates
git am /path/to/0001-add-overkill-factory-10-kanban-gates.patch
python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py
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

vFinal cards opt into the newer modular model with:

```json
{
  "factory_method_version": "OVERKILL_VFINAL"
}
```

The vFinal local hook, clean proof, disposable adapter runtime smoke,
disposable installed-Hermes CLI/Kanban smoke, real blocked worker-subtask
materialization smoke, block/unblock idempotency smoke and dashboard/API
`ready` route-parity smoke have passed. Worker-result ingestion from completed
subtasks has also passed with synthetic structured worker metadata. A dispatcher
route smoke has passed with a stubbed spawn function and proved worker subtasks
can be claimed after fixing dependency direction. A real-process auth-block
smoke has passed and proved the default spawn path starts a Hermes worker
process and blocks safely when the disposable profile has no provider/model.
The worker route readiness preflight has also run twice: first as a safe
`BLOCKED` receipt when the disposable profiles had no config, then as a
local-stub `PASS` receipt after all 23 disposable profiles were provisioned with
provider, model and local OpenAI-compatible `/models` evidence. Real validation
now has live profile/provider model auth across every non-human vFinal profile,
local terminal-tool auth for one bounded worker, and parent reconciliation from
a sanitized real worker result. It also has scanner-backed specialist quality
for one bounded public-safety path. The synthetic dispatch-completion smoke
additionally proves one claimed materialized worker subtask can complete with
structured metadata and emit parent ingestion evidence. The real-process
local-stub smoke proves the same completion/ingestion path through a real Hermes
child process and streaming `kanban_complete` tool call. The real-process
matrix local-stub smoke proves all 23 vFinal workers can complete through that
same real-child-process local-stub path. The service rollback drill proves a
disposable rollback-by-release-restore path and restores the patched state
after the drill. The real production rollback/monitoring smoke proves the
gateway can recover under systemd `Restart=always` and pass post-recovery
Hermes/Kanban health checks.

## Known Gap

The committed runtime patch proves the gate model and exit-code enforcement.
The transition-plan fixtures prove the intended fan-out and reconciliation
contract.

Real Hermes production integration is still not fully landed. The public adapter
now provides the executable hook, ledger contract, Kanban task JSON bridge,
vFinal smoke, clean proof, disposable adapter runtime smoke, Hermes v0.16
candidate patches, a disposable installed-Hermes CLI/Kanban smoke and a
disposable real worker-subtask materialization smoke plus idempotency smoke for
a second CLI gate pass, dashboard/API `ready` route parity, worker-result
ingestion, stubbed dispatcher route proof, real-process auth-block proof and a
worker-route readiness preflight plus a local-stub profile readiness PASS. The
synthetic dispatch-completion smoke now also proves dispatcher claim,
synthetic completion and parent ingestion in one path. The real-process
local-stub smoke now proves real child-process completion through
`kanban_complete` and parent ingestion, and the matrix variant proves the same
for all 23 worker routes. The service rollback drill now proves disposable
rollback-by-release-restore choreography. The dashboard create-route smoke now
proves `POST /tasks` cannot bypass before-ready creation, the dashboard
dispatch-route smoke proves `POST /dispatch` uses the same dispatcher mechanics,
the dashboard delete-route smoke proves `DELETE /tasks/{task_id}` cannot
hard-delete vFinal parent cards or worker subtasks, the dashboard links-route
smoke proves `POST /links` and `DELETE /links` cannot manually alter vFinal
worker dependencies, the dashboard attachment-route smoke proves upload/delete
path safety for evidence files, the dashboard bulk-archive smoke proves
`POST /tasks/bulk archive=True` cannot hide vFinal cards or workers, the
dashboard reassign-route smoke proves execution identity cannot be manually
changed for vFinal cards/workers, the dashboard reclaim/terminate smoke proves
generic recovery controls cannot abort vFinal worker subtasks, the dashboard
specify-route smoke proves generic auxiliary specification cannot rewrite
vFinal cards/workers, the dashboard decompose-route smoke proves generic
auxiliary fan-out cannot create parallel vFinal graphs, the dashboard board-delete
guard proves generic board archive/delete cannot hide vFinal work, the dashboard
board-lifecycle smoke proves board metadata/current selection routes do not
mutate vFinal task graphs, the dashboard profile-routes smoke proves profile
metadata edits do not mutate vFinal task graphs, the dashboard orchestration
smoke proves Kanban orchestration settings do not mutate vFinal task graphs,
and the dashboard done-route smoke now proves
`status=done` parity after patch `0007` fixes the dashboard import dependency.
The compatibility check now also treats the installed-runtime receipt bundle as
a checked contract, not just a documentation folder. The remaining work is to
prove Operator Control Tower readiness, turn the blocked update receipt into a
passing complete update receipt, satisfy the real-runtime update preflight, and keep future
dashboard/API route additions covered beyond
the covered attachment-safety, create, delete, dependency-links, dispatch, bulk
archive, reassign, reclaim/terminate, specify, decompose, comments,
home-subscribe, board-delete, board-lifecycle, profile-routes, orchestration,
`ready` and `done` paths.
