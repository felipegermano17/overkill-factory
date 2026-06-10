# Hermes Transition Plan Validation

This note defines what the public validation fixtures prove and what they do not
prove yet.

## What The Fixtures Prove

The transition-plan schema and hook result fixtures can represent two separate
runtime decisions:

- moving a card toward `ready`;
- moving a card toward `done`.

For `ready`, the fixture shows a plan with:

- `transition_action: allow_and_create_worker_tasks`;
- one `worker_subtask` per required worker;
- a `queue_class` for each subtask;
- a `required_before` value;
- the worker packet the runtime should hand to the worker;
- the expected Receipt Five field for the worker result.

For `done`, the fixture shows:

- `transition_action: block_transition` when required results are missing;
- `completion_reconciliation` listing required workers;
- per-worker satisfaction status;
- missing blocking workers;
- evidence refs when a result exists.

That means the model can distinguish planning, execution requests and closure
evidence. It avoids the common failure where a generated worker packet is
mistaken for proof that the worker already ran.

The hook fixtures under `validation/hermes-hook/` additionally prove:

- the runtime can persist an idempotent worker ledger;
- retrying the same transition does not create duplicate task ids;
- a blocked `done` transition exposes missing worker results;
- `--enforce` can make blocked transitions fail at process level.

The Kanban event bridge additionally proves that a Hermes task JSON payload can
be adapted into the same transition hook when the factory card is stored in the
task body.

The disposable adapter runtime smoke under
`validation/hermes-disposable-runtime/` proves the full repository-local adapter
contract:

- a ready vFinal card creates worker ledger rows;
- retrying the same ready transition creates no duplicate rows;
- missing security, access and autonomy readiness evidence blocks before ready;
- missing Control Tower evidence blocks owner-interface workers before ready;
- a done transition without worker results blocks;
- complete worker results plus Receipt Five allow done;
- Kanban task JSON can drive both ready and done through the same hook.

The Hermes v0.16 patch receipt under
`validation/hermes-v016-transition-patch/` proves the candidate installed-runtime
patch artifact:

- the patch file uses public paths;
- the patch has no private local path markers;
- the patch applies to a clean Hermes v0.16 `kanban_db.py`;
- the patched file compiles;
- the patch covers direct `ready` creation, automatic ready recompute, manual
  promote, unblock-to-ready and done transitions.

The disposable installed-Hermes smoke under
`validation/hermes-installed-runtime-smoke/` proves the CLI/Kanban path in an
installed but isolated Hermes runtime:

- direct `ready` creation blocks weak vFinal cards;
- complete vFinal cards are allowed into `ready`;
- allowed `ready` creates worker ledger rows;
- weak `done` blocks without receipt metadata;
- `done` is allowed when Receipt Five and worker results are supplied;
- manual unblock-to-ready rechecks the same gate;
- automatic dependency recompute to `ready` rechecks the same gate;
- block events, hook receipts and worker ledger files are written;
- patch reversal rollback compiles and removes the gate markers in the
  disposable runtime.

## Required Runtime Behavior

A real Hermes integration should implement this sequence:

```text
ready event
-> call adapters/hermes/transition_hook.py
-> persist or update worker ledger rows
-> map ledger rows to Hermes subtasks by queue class
-> allow ready only when before-ready blockers are satisfied

done event
-> call adapters/hermes/transition_hook.py with Receipt Five and worker results
-> reconcile expected Receipt Five fields and worker result artifacts
-> block missing or weak evidence
-> allow done only after Receipt Five and worker evidence agree
```

## What Still Needs Live Proof

The current public repository has schemas, examples, validation results, an
executable transition hook, a Kanban task JSON bridge, a disposable adapter
runtime smoke, a disposable installed-Hermes CLI/Kanban smoke, a disposable
worker-subtask materialization smoke and a disposable block/unblock idempotency
smoke. It also has a disposable dashboard/API `status=ready` route-parity smoke
and disposable worker-result ingestion, stubbed dispatcher-route and
real-process auth-block smokes, plus a worker-route readiness preflight that
first blocked all 23 unconfigured vFinal worker routes and then passed for all
23 disposable profiles after local-stub profile/config/model/provider
provisioning. A synthetic dispatcher-completion smoke now also proves one
claimed materialized worker subtask can complete with structured metadata and
emit parent ingestion evidence. The real-process matrix local-stub smoke proves
that same child-process/tool-loop path across all 23 vFinal workers, and the
service rollback drill proves disposable rollback-by-release-restore
choreography. Patch `0007` fixes the missing dashboard `python-multipart`
dependency, and the dashboard done-route smoke proves `status=done` parity.

Still needed:

- queue routing for `blocking-before-ready`, `blocking-before-done` and
  `advisory-review`;
- real autonomous specialist output quality after worker-result ingestion;
- real tool auth for materialized worker subtasks;
- enforcement parity across worker routes and remaining dashboard/API routes
  beyond the covered `ready` and `done` paths;
- blocked-state messages that identify the missing input or missing evidence;
- wider dashboard/API/worker-route parity;
- production service-manager rollback/monitoring proof beyond the disposable
  rollback drill;
- live evidence reconciliation before any production claim.

## Pass Criteria For The Next Live Smoke

The next live Hermes smoke should pass only when:

- a public-safe card moving toward `ready` creates the expected worker subtasks;
- retrying the same transition does not duplicate subtasks;
- before-ready blockers prevent `ready`;
- before-done worker tasks do not prevent `ready`, but do prevent weak `done`;
- partial worker results produce a blocked done reconciliation;
- completed worker results plus complete Receipt Five produce `allow_done`;
- worker-route readiness passes before any worker subtasks are born `ready`;
- CLI, dashboard and API paths return the same decision for more than the
  `status=ready` route already covered.

The repository-local disposable adapter smoke already proves the hook/bridge
decision layer. The installed-Hermes CLI/Kanban smoke proves the main CLI state
transitions in an isolated installed runtime. The worker-subtask smoke proves
real Hermes task materialization in blocked no-spawn mode. The idempotency smoke
proves a second CLI gate pass does not duplicate child links. The dashboard
route-parity smoke proves `status=ready` and bulk `status=ready` cannot bypass
the gate. The worker-result ingestion smoke proves completed worker subtasks can
write parent worker-result artifacts and parent `done` can find them
automatically. The stubbed dispatcher-route smoke proves spawnable materialized
workers can be claimed after fixing dependency direction. The real-process
auth-block smoke proves the default spawn path starts a Hermes worker process
and blocks safely when no provider/model is configured. The worker-route
readiness receipts prove both sides of the preflight: 23/23 routes block when
unconfigured, and 23/23 routes pass in a disposable local-stub setup after
profile/config/model/provider provisioning. The synthetic dispatch-completion
smoke proves claim -> completion -> parent ingestion wiring in one path. The
real-process local-stub smoke proves the same completion path through a real
Hermes child process and `kanban_complete` tool call. The matrix local-stub
smoke repeats that path for all 23 vFinal workers. The later real profile
auth matrix proves live model/provider reachability for the 46 non-human
vFinal profiles. The next live smoke must prove real tool auth, real specialist
output quality and wider dashboard/API route parity.
