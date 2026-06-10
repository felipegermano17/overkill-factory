# Hermes Adapter

Hermes is the required first runtime for Overkill Factory.

Use Hermes Kanban as the factory floor:

- Cards hold the work contract.
- Status transitions are authority boundaries.
- Gates block weak cards before execution.
- Done requires evidence, not prose.

Factory 10 was first proven on a Hermes checkout:

```text
branch: codex/overkill-factory-10-gates
commit: d297c0c78900d6858384297895ef4392e6fb85b9
```

Portable patch:

```text
adapters/hermes/patches/0001-add-overkill-factory-10-kanban-gates.patch
```

Validation command used:

```bash
venv/bin/python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py
```

Expected result: `72 passed`.

Factory vFinal candidate patch:

```text
adapters/hermes/patches/0002-add-overkill-vfinal-kanban-transition-hook.patch
adapters/hermes/patches/0003-materialize-overkill-vfinal-worker-subtasks.patch
adapters/hermes/patches/0004-guard-overkill-vfinal-dashboard-ready-route.patch
adapters/hermes/patches/0005-ingest-overkill-worker-results-from-subtasks.patch
adapters/hermes/patches/0006-fix-overkill-worker-subtask-dependency-direction.patch
```

Patch-level evidence:

```text
validation/hermes-v016-transition-patch/patch-apply-receipt.json
```

This proves the vFinal `kanban_db.py` patch applies to a clean Hermes v0.16 file
and compiles. The patch covers direct `ready` creation, automatic ready
recompute, manual promote, unblock-to-ready and done transitions. Validate the
dashboard/API route patch separately with
`adapters/hermes/validate_v016_dashboard_route_patch.py`.

Installed disposable CLI/Kanban proof is recorded at:

```text
validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json
```

This proves direct `ready` blocking, positive `ready` allowance with worker
ledger creation, weak `done` blocking, positive `done` allowance with Receipt
Five plus worker results, unblock-to-ready blocking and recompute-to-ready
blocking through the installed CLI/Kanban path. It also proves patch reversal
rollback in the disposable runtime. It still does not prove production
readiness.

Worker-subtask materialization proof is recorded at:

```text
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
```

This proves `0002` plus `0003` can create 23 real Hermes worker subtasks from a
fresh vFinal `ready` card and keep them blocked by default. It also proves a
second CLI gate pass through `block -> unblock` reuses those worker subtasks
instead of duplicating them. Patch `0004` proves dashboard/API `status=ready`
and bulk `status=ready` cannot bypass the gate. Patch `0005` proves completed
worker subtasks can write parent worker-result artifacts for done
reconciliation. Patch `0006` fixes dependency direction so worker subtasks are
prerequisites of the parent Factory card, and the stubbed dispatcher-route smoke
proves spawnable materialized workers can be claimed. The real-process
auth-block smoke proves the default spawn path starts a Hermes worker process
and blocks safely when no provider/model is configured. The readiness preflight
first proved 23/23 unconfigured routes stay blocked, then the local-stub
profile readiness smoke proved 23/23 disposable worker profiles can pass with
explicit provider, model and local `/models` evidence. The synthetic
dispatch-completion smoke proves one materialized worker can be claimed,
completed with structured metadata and ingested by the parent. The real-process
local-stub smoke proves the default dispatcher can spawn a real Hermes child,
the child can receive the `kanban_complete` tool surface, complete the worker
task through a local OpenAI-compatible streaming stub, and trigger parent
worker-result ingestion. The matrix version proves that same path for all 23
vFinal workers. Non-stub model execution, real tool auth, real specialist
output quality, wider route parity and real-service rollback remain required
before a real Hermes update.

Worker-route readiness is now a hard preflight before enabling production
dispatch:

```bash
python adapters/hermes/worker_route_readiness.py \
  --ledger validation/hermes-disposable-runtime/worker-ledger.json \
  --hermes-home /path/to/disposable/hermes/home
```

If the result is `BLOCKED`, keep `OVERKILL_FACTORY_WORKER_TASK_STATUS=blocked`.
If a local-stub smoke returns `PASS`, treat it as permission for the next
disposable smoke only, not as production approval.

When operating Overkill/Hermes, also use the `hermes-kanban` skill.
