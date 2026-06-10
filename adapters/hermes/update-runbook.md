# Hermes Update Runbook

Do not update a real Hermes factory runtime directly.

## Order

1. Identify the current Hermes version and target Hermes version.
2. Create or use a disposable Hermes checkout/runtime.
3. Apply the Overkill adapter patches.
4. Run compatibility checks, including adapter markers, route inventory and
   installed-runtime receipt bundle status.
5. Run local negative and positive adapter smokes, including the Kanban event
   bridge and disposable adapter runtime smoke.
6. Install the same hook path into a disposable Hermes runtime.
7. Run live disposable Hermes smokes through real Kanban state.
8. Run worker-route readiness against the disposable worker ledger and Hermes
   home.
9. Run the local-stub worker profile readiness smoke in the disposable runtime.
10. Run the synthetic dispatcher-completion smoke in the disposable runtime.
11. Run the real-process local-stub worker completion smoke in the disposable
    runtime.
12. Run the real-process matrix local-stub smoke across all vFinal workers.
13. Record the update receipt.
14. Run the production update preflight with real proof refs.
15. Decide whether to update the real runtime.
16. Keep rollback ready until the first post-update factory card succeeds.

## Integration Target

Do not install the Factory gate as a generic shell hook and call that done.

Shell hooks can guard agent/tool events, but Factory vFinal needs a Kanban
transition hook at the shared `ready` and `done` decision point. The installed
runtime path must protect CLI, dashboard, API and worker routes together.

See `kanban-transition-hook-integration.md`.

## Required Patches

There are two patch families:

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

`0001` is the legacy Factory 10 patch.

For the current vFinal Hermes v0.16 validation path, apply `0002` and then
`0003`, then `0005`, then `0006` to a clean Hermes v0.16 `kanban_db.py`, apply
`0004`, `0008`, `0009`, `0010`, `0011`, `0012`, `0013`, `0014`, `0015` and
`0016` to a clean Hermes v0.16
`plugins/kanban/dashboard/plugin_api.py`, and apply `0007` to the checkout
dependency files before dashboard smokes. Do not apply `0001` first unless
there is a separate combined-patch merge proof.

`0002` is an opt-in candidate patch. It requires:

```text
OVERKILL_FACTORY_KANBAN_GATE=1
OVERKILL_FACTORY_ADAPTER_ROOT=/path/to/overkill-factory
```

`0003` is a second opt-in layer. It turns the vFinal worker ledger into real
Hermes subtasks only when explicitly enabled:

```text
OVERKILL_FACTORY_CREATE_WORKER_TASKS=1
OVERKILL_FACTORY_WORKER_TASK_STATUS=blocked
```

Keep the worker task status `blocked` until the factory proves worker-route
parity and worker-route readiness. Do not let worker subtasks spawn just
because materialization works.

`0004` guards dashboard/API `status=ready`. It prevents dashboard drag/drop or
bulk update from writing `ready` directly for Overkill vFinal cards.

`0005` ingests completed Overkill worker subtasks into parent worker-result
artifacts so parent `done` reconciliation can find the evidence automatically.

`0006` fixes worker-subtask dependency direction. Worker subtasks must be
parents of the Factory card, not children blocked by it. Without this patch,
autonomous worker dispatch can deadlock behind the card that is waiting for the
worker evidence.

`0007` adds `python-multipart` to the Hermes `web` extra so dashboard routes
that declare FastAPI `File/Form` parameters can import before route parity is
tested.

`0008` guards dashboard/API `DELETE /tasks/{task_id}`. It blocks hard-delete for
vFinal parent cards and worker subtasks, while leaving ordinary non-factory task
deletion available.

`0009` guards dashboard/API `POST /links` and `DELETE /links`. It blocks manual
dependency-link edits that touch vFinal parent cards or worker subtasks, while
leaving ordinary non-factory dependency links available.

`0010` guards dashboard/API `DELETE /attachments/{attachment_id}`. It refuses
delete when an attachment row points outside the board attachment root, while
leaving ordinary attachment upload/delete behavior available.

`0011` guards dashboard/API `POST /tasks/bulk` with `archive=True`. It blocks
bulk archive for vFinal parent cards and worker subtasks, while leaving ordinary
non-factory task archive available.

`0012` guards dashboard/API `POST /tasks/{task_id}/reassign`. It blocks manual
execution-profile changes for vFinal parent cards and worker subtasks, while
leaving ordinary non-factory task reassign available.

`0013` guards dashboard/API `POST /tasks/{task_id}/reclaim` and
`POST /runs/{run_id}/terminate`. It blocks generic abort/recovery controls for
vFinal worker subtasks, while leaving ordinary non-factory recovery available.

`0014` guards dashboard/API `POST /tasks/{task_id}/specify`. It blocks generic
auxiliary specification/rewrite for vFinal parent cards and worker subtasks,
while leaving ordinary non-factory specify behavior available.

`0015` guards dashboard/API `POST /tasks/{task_id}/decompose`. It blocks
generic auxiliary task-graph fan-out for vFinal parent cards and worker
subtasks, while leaving ordinary non-factory decompose behavior available.

`0016` guards dashboard/API `DELETE /boards/{slug}`. It blocks archive and
hard-delete for boards containing vFinal parent cards or worker subtasks, while
leaving ordinary disposable board archive/delete behavior available.

Before touching any real runtime, validate the patch artifact against a clean
Hermes v0.16 checkout:

```bash
python adapters/hermes/validate_v016_transition_patch.py \
  --source-kanban-db /path/to/hermes_cli/kanban_db.py \
  --out validation/hermes-v016-transition-patch/patch-apply-receipt.json

python adapters/hermes/validate_v016_dashboard_route_patch.py \
  --source-plugin-api /path/to/plugins/kanban/dashboard/plugin_api.py \
  --out validation/hermes-v016-transition-patch/dashboard-route-patch-apply-receipt.json
```

Patch-level `PASS` means the patch applies and compiles. It does not mean the
installed runtime is production-ready.

When applying patches for an installed-runtime smoke, run from a real disposable
checkout root or initialize the disposable tree with its own `.git` directory
first. Do not trust `git apply` from a folder nested inside another repository;
it can target the parent repository and create a false success.

## Required Smokes

1. Product-facing card without `product_face_packet` fails before `ready`.
2. Self-review card fails before `ready`.
3. Completion without `receipt_five` and `kanban_transition_event` fails before `done`.
4. Security-required card cannot close without `security_scan_result`.
5. R4 card without `r4_gate` fails.
6. vFinal material execution without `security_architecture_plan` fails before
   `ready`.
7. vFinal material execution without ready `access_capability` and
   `autonomy_readiness_packet` fails before `ready`.
8. vFinal R3 ready card creates real blocked Hermes worker subtasks for Method
   Router, Access, Security Architecture, Budget, Agent Eval, Data/Metrics and
   Factory Maturity.
9. vFinal Control Tower card blocks when owner interface projection, event,
   approval and Discord mapping evidence are missing.
10. vFinal done blocks when required worker results are missing.
11. vFinal done allows only when Receipt Five and required worker results agree.
12. Kanban task JSON bridge returns the same ready/done decision as the direct
   transition hook.
13. Blocked transition leaves the card blocked and emits a machine-readable
    block event. Until Hermes returns non-zero consistently for every refused
    transition, automation must verify `show --json` state and events after the
    command.
14. Dashboard/API `status=ready` path cannot bypass the same gate.
15. `create_task` cannot create a Factory card directly in `ready` without the
    same gate.
16. `recompute_ready` cannot auto-promote a Factory card without the same gate.
17. `unblock_task` cannot move a Factory card from `blocked`/`scheduled` to
    `ready` without the same gate.
18. Worker-route readiness blocks production dispatch when required worker
    profiles, configs, models, providers or credential/reachable-local-endpoint
    evidence are missing.
19. Local-stub worker profile readiness can provision all required disposable
    worker profiles and pass `/models` evidence without touching the real
    Hermes runtime.
20. Synthetic dispatcher-completion proves a claimed materialized worker can
    complete with structured metadata and emit parent ingestion evidence.
21. Dashboard/API `DELETE /tasks/{task_id}` cannot hard-delete vFinal parent
    cards or worker subtasks.
22. Dashboard/API `POST /links` and `DELETE /links` cannot manually edit
    dependency links that touch vFinal parent cards or worker subtasks.
23. Dashboard/API attachment upload/delete keeps uploaded files under the board
    attachment root and blocks tampered outside-root delete.
24. Dashboard/API bulk `archive=True` cannot archive vFinal parent cards or
    worker subtasks.
25. Dashboard/API reassign cannot manually change execution profile for vFinal
    parent cards or worker subtasks.
26. Dashboard/API reclaim and run terminate cannot abort vFinal worker subtasks
    through generic recovery controls.
27. Dashboard/API specify cannot rewrite or promote vFinal parent cards or
    worker subtasks through the generic auxiliary specifier route.
28. Dashboard/API decompose cannot create a parallel task graph for vFinal
    parent cards or worker subtasks through the generic auxiliary decomposer.
29. Dashboard/API comments remain append-only for vFinal parent cards and
    worker subtasks; comments do not become authoritative gate evidence.
30. Dashboard/API home-subscribe toggles remain visibility-only for vFinal
    parent cards and worker subtasks; notification routing does not become
    task authority.
31. Dashboard/API board archive/delete cannot hide or destroy boards that
    contain vFinal parent cards or worker subtasks through generic board
    controls.
32. Dashboard/API board create, metadata patch and switch remain metadata/current
    pointer operations; they do not mutate existing vFinal task graphs, worker
    subtasks or dependency links.
33. Dashboard/API profile patch and auto-description remain profile metadata
    operations; they do not mutate existing vFinal task graphs, worker subtasks
    or dependency links.
34. Dashboard/API orchestration settings remain Kanban config operations; they
    reject missing profile overrides before save and do not mutate existing
    vFinal task graphs, worker subtasks or dependency links.

## Local Adapter Smoke

Before installing anything into Hermes, run:

```bash
python adapters/hermes/disposable_runtime_smoke.py
python adapters/hermes/validate_v016_transition_patch.py --source-kanban-db /path/to/hermes_cli/kanban_db.py
```

This proves the repository-local adapter contract only. It covers before-ready,
idempotent retry, before-ready blocking, Control Tower blocking, before-done
blocking, before-done `allow_done` with worker results, and Kanban task JSON
bridge behavior.

It does not prove that an installed Hermes runtime calls the hook automatically.
That proof must happen in a disposable Hermes runtime.

## Installed Runtime Smoke

The current public-safe disposable installed-Hermes CLI/Kanban receipt is:

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
validation/hermes-installed-runtime-smoke/dashboard-route-inventory-smoke.json
validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json
```

Read the current readiness matrix before any real-runtime decision:

```text
docs/validation/hermes-vfinal-production-readiness-status.md
```

Then run the production update preflight. With no real proof refs, it must stay
`BLOCKED`:

```bash
python adapters/hermes/production_update_preflight.py \
  --out validation/hermes-production-update-preflight/real-runtime-update-blocked.json
```

Only rerun it with proof refs when those proofs actually exist:

```bash
python adapters/hermes/production_update_preflight.py \
  --non-stub-worker-execution path/to/non-stub-worker-proof.json \
  --real-tool-auth path/to/tool-auth-proof.json \
  --specialist-output-quality path/to/specialist-quality-proof.json \
  --real-worker-done-reconciliation path/to/done-reconciliation-proof.json \
  --production-rollback-monitoring path/to/production-rollback-proof.json \
  --operator-control-tower path/to/control-tower-proof.json \
  --complete-update-receipt path/to/update-receipt.json
```

If the preflight result is `BLOCKED`, do not touch the real Hermes runtime.

Each proof ref, except the complete Hermes update receipt itself, must use the
production proof contract:

```text
schemas/hermes-production-proof.schema.json
templates/hermes-production-proof.json
```

The preflight rejects generic `PASS` JSON, mismatched proof types, missing
evidence refs, missing proof limits and blocked real-runtime decisions.

The first receipt proves:

- direct `ready` creation blocks weak vFinal cards;
- complete vFinal cards are allowed into `ready`;
- allowed `ready` creates worker ledger rows;
- weak `done` blocks without receipt metadata;
- `done` is allowed when Receipt Five and worker results are supplied;
- manual unblock-to-ready rechecks the gate;
- automatic dependency recompute to `ready` rechecks the gate;
- block events, hook receipts and worker ledger files are written;
- reversing the patch compiles and removes the gate markers in the disposable
  runtime.

It does not prove dashboard/API route parity outside the CLI/Kanban paths,
autonomous worker result ingestion or production service-manager rollback.

The second receipt proves:

- patches `0002` and `0003` apply in sequence and compile;
- a fresh vFinal `ready` card materializes 23 real Hermes worker subtasks;
- those subtasks are linked to the parent card;
- those subtasks are born `blocked`;
- the parent transition event records `materialized_worker_tasks`;
- the hook result reference is sanitized as `runtime-artifact:<task>/<file>`.

It does not prove that those subtasks can be safely dispatched/executed by real
workers. That is the next parity proof, not an assumption.

The third receipt proves:

- a second CLI gate pass through `block -> unblock` keeps the same 23 child task
  links;
- the retry creates zero new worker subtasks;
- the retry updates/reuses the 23 existing subtasks;
- worker subtasks remain `blocked`.

It does not prove idempotency through dashboard/API/worker routes.

The fourth receipt proves:

- before `0004`, dashboard/API `status=ready` could move a legacy/inconsistent
  weak vFinal card from `todo` to `ready` without a transition-gate event;
- after `0004`, the same weak card is refused with a gate event;
- after `0004`, a complete vFinal card is allowed to `ready` and materializes
  23 blocked worker subtasks;
- after `0004`, bulk `status=ready` also respects the gate.

It does not prove worker-result ingestion or dispatcher routing by itself; those
are covered by the fifth and sixth receipts.

The dashboard dependency patch receipt proves:

- `0007` adds `python-multipart` to the Hermes `web` extra;
- the dependency is required because the Kanban dashboard plugin uses FastAPI
  `File/Form` route parameters;
- without that dependency, the dashboard plugin can fail at import time before
  route parity can be tested.

The dashboard create-route parity receipt proves:

- dashboard/API `POST /tasks` does not expose a direct `status` field;
- weak vFinal direct ready creation is blocked by the before-ready gate;
- valid vFinal direct ready creation is allowed and materializes 23 blocked
  worker subtasks.

The dashboard dispatch-route parity receipt proves:

- dashboard/API `POST /dispatch` does not spawn blocked worker subtasks;
- dashboard/API `POST /dispatch` does not spawn the parent Factory card while
  worker prerequisites remain open;
- dashboard/API `POST /dispatch` can spawn one selected ready worker through a
  stubbed spawn function.

The dashboard done-route parity receipt proves:

- dashboard/API `status=done` refuses weak vFinal completion through the
  before-done gate;
- dashboard/API `status=done` allows valid completion when Receipt Five and
  worker-result metadata are supplied;
- bulk dashboard/API `status=done` also refuses weak completion.

The fifth receipt proves:

- a completed worker subtask can write a structured worker-result artifact under
  the parent runtime directory;
- child and parent tasks both receive `overkill_worker_result_ingested` events;
- all 13 before-done worker subtasks in the vFinal smoke can write results;
- parent `done` can reconcile those auto-ingested results without a manually
  supplied `worker_results_dir`.

It does not prove real profile availability, model execution or specialist
output quality.

The sixth receipt proves:

- `0006` changes worker dependencies to `worker subtask -> parent Factory card`;
- a parent Factory card with unfinished worker prerequisites is rejected from
  spawning and returns to `todo`;
- spawnable materialized worker subtasks can be claimed by the dispatcher;
- dispatcher claim/run events are written for the spawned worker subtasks.

It uses a stubbed spawn function and disposable profile directories. It does
not prove real Hermes child process execution, model/tool auth, specialist
quality or autonomous completion.

The seventh receipt proves:

- the default dispatcher spawn path starts a real Hermes worker process;
- the task records a worker PID and enters `running`;
- when the disposable profile has no provider/model credentials, the worker
  exits and the dispatcher records `crashed` plus `gave_up`;
- the task blocks after one failure instead of respawning forever.

It intentionally removes ambient provider credentials. It does not prove a real
model call, real tool auth, autonomous completion or specialist result quality.

The worker-route readiness receipt proves:

- 23/23 vFinal worker routes are currently blocked in the disposable runtime;
- existing disposable profile directories without `config.yaml` are still not
  considered ready;
- missing profile/config/model/provider readiness is machine-readable per
  worker;
- `OVERKILL_FACTORY_WORKER_TASK_STATUS=ready` must not be used in production
  while the readiness receipt is `BLOCKED`.

Run the preflight before any attempt to make materialized worker subtasks
spawnable:

```bash
python adapters/hermes/worker_route_readiness.py \
  --ledger validation/hermes-disposable-runtime/worker-ledger.json \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/worker-route-readiness-blocked.json
```

The local-stub worker profile readiness receipt proves:

- all 23 disposable worker profiles can be provisioned with `config.yaml`;
- each profile can use an explicit provider, model and local
  OpenAI-compatible `/models` endpoint;
- the same readiness preflight can return `PASS` when profile/config/model/
  provider shape is present.

It does not prove real model quality, real tool auth, autonomous completion or
production readiness.

Run it only against a disposable Hermes home:

```bash
python adapters/hermes/worker_profile_readiness_smoke.py \
  --ledger validation/hermes-disposable-runtime/worker-ledger.json \
  --hermes-home /path/to/disposable/hermes/home \
  --overwrite \
  --out validation/hermes-installed-runtime-smoke/worker-profile-readiness-local-stub-smoke.json
```

The synthetic dispatcher-completion receipt proves:

- a fresh vFinal card can materialize 23 worker subtasks as `ready` in a
  disposable runtime;
- the dispatcher can claim one materialized worker subtask;
- a synthetic worker completion can call the normal completion path with
  structured Overkill metadata;
- the parent card receives an `overkill_worker_result_ingested` event.

It does not prove real model execution, real tool auth or specialist quality.

Run it only against a disposable Hermes checkout/home:

```bash
python adapters/hermes/worker_dispatch_completion_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/worker-dispatch-completion-smoke.json
```

The real-process local-stub receipt proves:

- a fresh vFinal card can materialize worker subtasks in a disposable runtime;
- the real Hermes dispatcher can spawn one real child worker process;
- the real child sees the `kanban_complete` tool surface;
- a local OpenAI-compatible streaming stub can return a `kanban_complete`
  tool call;
- the child task reaches `done`;
- the parent receives `overkill_worker_result_ingested`.

It does not prove non-stub model quality, real tool auth, specialist reasoning
quality, cloud access, deployment, rollback or production readiness.

Run it only against a disposable Hermes checkout/home:

```bash
python adapters/hermes/worker_real_process_local_stub_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/worker-real-process-local-stub-smoke.json
```

The real-process matrix local-stub receipt proves the same child-process,
`kanban_complete` and parent-ingestion path across all 23 vFinal workers.

It is still local-stub evidence. It does not prove non-stub model quality, real
tool auth or production readiness.

Run it only against a disposable Hermes checkout/home:

```bash
python adapters/hermes/worker_real_process_matrix_local_stub_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/worker-real-process-matrix-local-stub-smoke.json
```

The dashboard done-route parity receipt proves dashboard/API `status=done`
uses the same before-done gate as the CLI/Kanban path.

The dashboard create-route parity receipt proves dashboard/API `POST /tasks`
uses the same before-ready gate as the CLI/Kanban creation path.
The dashboard dispatch-route parity receipt proves dashboard/API `POST /dispatch`
uses the same dispatcher mechanics as the CLI/Kanban dispatch path.
The dashboard delete-route guard receipt proves dashboard/API
`DELETE /tasks/{task_id}` blocks hard-delete for vFinal parent cards and worker
subtasks, preserves worker prerequisite links, and still allows normal
non-factory task deletion.
The dashboard links-route guard receipt proves dashboard/API `POST /links` and
`DELETE /links` block manual dependency-link edits that touch vFinal parent
cards or worker subtasks, preserve worker prerequisite links, and still allow
normal non-factory task links.
The dashboard attachment-route safety receipt proves dashboard/API
`POST /tasks/{task_id}/attachments` keeps traversal filenames under the board
attachment root, normal attachment delete works, and
`DELETE /attachments/{attachment_id}` blocks a tampered outside-root path.
The dashboard bulk-archive guard receipt proves dashboard/API `POST /tasks/bulk`
with `archive=True` blocks vFinal parent cards and worker subtasks, while normal
non-factory task archive still works.
The dashboard reassign-route guard receipt proves dashboard/API
`POST /tasks/{task_id}/reassign` blocks manual execution-profile changes for
vFinal parent cards and worker subtasks, while normal non-factory task reassign
still works.
The dashboard reclaim/terminate guard receipt proves dashboard/API
`POST /tasks/{task_id}/reclaim` and `POST /runs/{run_id}/terminate` block
generic abort/recovery for vFinal worker subtasks, while normal non-factory
task recovery still works.
The dashboard specify-route guard receipt proves dashboard/API
`POST /tasks/{task_id}/specify` blocks generic auxiliary rewrite/promotion for
vFinal parent cards and worker subtasks, while normal non-factory task specify
still works.
The dashboard decompose-route guard receipt proves dashboard/API
`POST /tasks/{task_id}/decompose` blocks generic auxiliary task-graph fan-out
for vFinal parent cards and worker subtasks, while normal non-factory task
decompose still works.
The dashboard comments append-only receipt proves dashboard/API
`POST /tasks/{task_id}/comments` stays available for vFinal parent cards,
worker subtasks and normal tasks, but only appends comment/event rows. It does
not change task status, body, assignee, dependency links or gate authority.
The dashboard home-subscribe visibility receipt proves dashboard/API
`POST /tasks/{task_id}/home-subscribe/{platform}` and
`DELETE /tasks/{task_id}/home-subscribe/{platform}` stay available for owner
visibility, but only add/remove notification subscription rows. They do not
change task status, body, assignee, dependency links or gate authority.
The dashboard board-delete guard receipt proves dashboard/API
`DELETE /boards/{slug}` blocks archive and hard-delete for boards containing
vFinal parent cards or worker subtasks, while ordinary disposable boards can
still be archived or deleted. The receipt redacts local archive paths.
The dashboard board-lifecycle operational-safety receipt proves dashboard/API
`POST /boards`, `PATCH /boards/{slug}` and `POST /boards/{slug}/switch` only
create board metadata, update display metadata or change the current-board
pointer. They do not mutate existing vFinal task graphs, worker subtasks or
dependency links.
The dashboard profile-routes operational-safety receipt proves dashboard/API
`PATCH /profiles/{profile_name}` and
`POST /profiles/{profile_name}/describe-auto` only update profile metadata.
The auto-description success path uses a local stub, so this is route-safety
proof, not real auxiliary model-quality proof.
The dashboard orchestration-route operational-safety receipt proves
dashboard/API `PUT /orchestration` only updates Kanban orchestration config
knobs. Missing profiles are rejected before save, valid settings are persisted,
overrides can be cleared, and existing vFinal task graphs are not mutated.
The dashboard route inventory receipt must stay at 0 pending mutating route
families. `adapters/hermes/compatibility-check.py` enforces this so any future
dashboard/API route addition must be explicitly classified and proven before a
real runtime update.

The same compatibility check also enforces the installed-runtime receipt
bundle. Required proof receipts must remain `PASS`, the worker-route readiness
block receipt must remain `BLOCKED`, and unexpected `FAIL` or new blocked
receipts stop the update until they are understood and resolved.

Run these route smokes only against a disposable Hermes checkout/home with
patches `0007`, `0008`, `0009`, `0010`, `0011`, `0012`, `0013`, `0014`, `0015`
and `0016` applied and
`python-multipart` installed through the Hermes `web` extra:

```bash
python adapters/hermes/dashboard_create_route_parity_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-create-route-parity-smoke.json

python adapters/hermes/dashboard_dispatch_route_parity_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-dispatch-route-parity-smoke.json

python adapters/hermes/dashboard_delete_route_guard_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-delete-route-guard-smoke.json

python adapters/hermes/dashboard_links_route_guard_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-links-route-guard-smoke.json

python adapters/hermes/dashboard_attachment_route_safety_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-attachment-route-safety-smoke.json

python adapters/hermes/dashboard_bulk_archive_guard_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-bulk-archive-guard-smoke.json

python adapters/hermes/dashboard_reassign_route_guard_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-reassign-route-guard-smoke.json

python adapters/hermes/dashboard_reclaim_terminate_guard_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-reclaim-terminate-guard-smoke.json

python adapters/hermes/dashboard_specify_route_guard_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-specify-route-guard-smoke.json

python adapters/hermes/dashboard_decompose_route_guard_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-decompose-route-guard-smoke.json

python adapters/hermes/dashboard_comments_route_append_only_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-comments-route-append-only-smoke.json

python adapters/hermes/dashboard_home_subscribe_route_visibility_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-home-subscribe-route-visibility-smoke.json

python adapters/hermes/dashboard_board_delete_route_guard_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-board-delete-route-guard-smoke.json

python adapters/hermes/dashboard_board_lifecycle_operational_safety_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-board-lifecycle-operational-safety-smoke.json

python adapters/hermes/dashboard_profile_routes_operational_safety_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-profile-routes-operational-safety-smoke.json

python adapters/hermes/dashboard_orchestration_route_operational_safety_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-orchestration-route-operational-safety-smoke.json

python adapters/hermes/dashboard_done_route_parity_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --out validation/hermes-installed-runtime-smoke/dashboard-done-route-parity-smoke.json
```

The service rollback drill receipt proves a disposable
rollback-by-release-restore path:

- the Hermes checkout/home/baseline inputs are guarded as disposable `.tmp`
  paths;
- the patched adapter files are backed up;
- clean baseline source files are restored;
- `py_compile`, `kanban_db` import and `hermes version` health checks pass
  after rollback;
- a service-like process can start and stop with isolated `HOME` and
  `HERMES_HOME`;
- the patched adapter state is restored after the drill.

It does not prove a real systemd unit, Windows service, Discord gateway,
monitoring stack, cloud rollback or production rollback.

Run it only against a disposable Hermes checkout/home and a clean disposable
baseline tree:

```bash
python adapters/hermes/service_rollback_drill_smoke.py \
  --hermes-checkout /path/to/disposable/hermes/checkout \
  --hermes-home /path/to/disposable/hermes/home \
  --baseline-tree /path/to/disposable/clean/hermes/tree \
  --out validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json
```

## Dispatch Dry-Run Caveat

Use `dispatch --dry-run` only on disposable boards. It can be useful to inspect
what would spawn, but it must not be treated as a zero-mutation read-only
operation on an important board. A runtime smoke must verify the card history
after dry-run before claiming that no transition side effect occurred.

Do not rely on `--initial-status blocked` as a durable no-spawn hold. In Hermes
runtimes where `blocked` tasks are recomputed, a task can be promoted unless a
real `blocked` event exists in its history. For no-spawn smoke cards, create the
task, call `kanban block <task> <reason>`, and verify the `blocked` event before
running any dispatch check.

## What To Adopt From New Hermes Releases

Adopt new Hermes features only when they map to a factory use case:

- dashboard: human supervision and gate visibility;
- admin controls: runtime safety and profile hygiene;
- memory controls: trust tier, freshness and poisoning review;
- remote gateway: remote proof and controlled operator access;
- update checks: compatibility receipt and rollback workflow;
- security fixes: always reviewed, never blindly merged.

## Rollback Rule

If any gate bypass, exit-code regression, missing symbol or public-safety leak is
found, the update is blocked. Roll back or keep the factory on the previous
runtime until the adapter is repaired.
