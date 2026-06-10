# Overkill Factory

Overkill Factory is an open product-production factory for autonomous agents.

It turns a messy product paper into a controlled production line:

```text
raw product paper
-> source ledger and source resolution
-> outcome and Product SOT
-> Agentic Method Router and Method Contract
-> architecture, security and product-experience plans
-> autonomy, access and budget readiness
-> Hermes worker routes and factory cards
-> agent execution with worker subtasks
-> worker results, verification and review
-> Receipt Five and Completion Audit
-> owner approvals and Operator Control Tower
-> release, monitoring and learnback
```

The core belief is simple: autonomous agents do not need prettier prose. They
need contracts, gates, receipts, and a runtime that refuses weak work.

## What This Repository Contains

- The Overkill Factory methodology.
- Machine-checkable card and receipt contracts.
- Hermes/Kanban adapter patches.
- Example cards, worker packets, gate reports, and Receipt Five metadata.
- A Codex skill for operating the factory.
- Initial automation for critical factory workers: Product Face, Codex Security,
  onchain auditor, independent reviewer, and human gate clerk.
- Factory 11 hardening: public source policy, security control matrix, worker
  registry, Hermes update safety, public-safety scan and CI.
- Heavy validation battery artifacts with Product Face, security, onchain,
  release, agentic and public-repo stress scenarios.

## Why Hermes Is Required

The first supported runtime is Hermes.

Hermes is the factory floor: the agents live there, the work moves through its
Kanban, and the gates block bad transitions before autonomous execution starts.

Overkill Factory stays separate from Hermes so the methodology remains its own
project, but the Hermes adapter is a first-class and required integration.

## Current Status

Factory 10 has been validated in a real Hermes runtime.

The portable Hermes adapter patch is kept under `adapters/hermes/patches/`.

Factory vFinal now has candidate Hermes v0.16 patches for the Kanban
transition gate, worker-subtask materialization, dashboard/API ready-route
guarding, worker-result ingestion and worker dependency direction:

```text
adapters/hermes/patches/0002-add-overkill-vfinal-kanban-transition-hook.patch
adapters/hermes/patches/0003-materialize-overkill-vfinal-worker-subtasks.patch
adapters/hermes/patches/0004-guard-overkill-vfinal-dashboard-ready-route.patch
adapters/hermes/patches/0005-ingest-overkill-worker-results-from-subtasks.patch
adapters/hermes/patches/0006-fix-overkill-worker-subtask-dependency-direction.patch
```

Patch-level evidence shows the vFinal patch artifacts apply to clean Hermes
v0.16 `kanban_db.py` and `plugin_api.py` files and compile:

```text
validation/hermes-v016-transition-patch/patch-apply-receipt.json
validation/hermes-v016-transition-patch/dashboard-route-patch-apply-receipt.json
```

Disposable installed-Hermes CLI/Kanban evidence now shows the patch blocks weak
Factory cards during direct `ready` creation, automatic ready recompute, manual
unblock-to-ready and weak `done` attempts. It also allows a complete vFinal card
through `ready`, creates worker ledger rows, and allows `done` when Receipt Five
and worker result artifacts are supplied:

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
```

Control Tower read-only evidence now proves the owner cockpit can derive a
project projection, owner event, approval request and redacted Discord mapping
from runtime-shaped state without claiming any Discord-side mutation:

```text
validation/control-tower/control-tower-readonly-smoke.json
```

Control Tower approval-contract evidence proves a structured owner approval can
produce a runtime-registerable event only when approval id, owner role, scope
and expiry match. Wrong role, expired request, scope expansion, unknown
approval id and ambiguous decision are rejected:

```text
validation/control-tower/control-tower-approval-registration-smoke.json
```

The worker-subtask smoke proves 23 real Hermes worker subtasks can be created
from the vFinal ledger and born `blocked` by default.

The idempotency smoke proves a second gate pass through `block -> unblock`
reuses the same 23 child task links instead of duplicating worker subtasks.

The dashboard route-parity smoke proves dashboard/API `status=ready` cannot
bypass the vFinal gate, including bulk updates.

The dashboard create-route parity smoke proves dashboard/API `POST /tasks`
does not expose a `status` field, weak direct ready creation is blocked by the
gate, and valid direct ready creation materializes 23 blocked worker subtasks.

The dashboard dispatch-route parity smoke proves dashboard/API `POST /dispatch`
does not spawn blocked worker subtasks, does not spawn the parent Factory card
while worker prerequisites remain open, and only spawns a selected ready worker
through a stubbed spawn function.

The dashboard delete-route guard smoke proves dashboard/API
`DELETE /tasks/{task_id}` cannot hard-delete vFinal parent cards or worker
subtasks, keeps worker prerequisite links intact, and still allows ordinary
non-factory disposable tasks to be deleted.

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
still be archived or deleted. Its receipt redacts local board archive paths.

The dashboard board-lifecycle operational-safety smoke proves dashboard/API
`POST /boards`, `PATCH /boards/{slug}` and `POST /boards/{slug}/switch` only
create board metadata, update display metadata or change the current-board
pointer. They do not mutate existing vFinal task graphs, worker subtasks or
dependency links.

The dashboard profile-routes operational-safety smoke proves dashboard/API
`PATCH /profiles/{profile_name}` and
`POST /profiles/{profile_name}/describe-auto` only update profile metadata.
The auto-description success path is stubbed locally, so it proves route safety
without using a real auxiliary model or credentials.

The dashboard orchestration-route operational-safety smoke proves dashboard/API
`PUT /orchestration` only updates Kanban orchestration config knobs. Missing
profiles are rejected before save, valid settings are persisted, overrides can
be cleared, and existing vFinal task graphs are not mutated.

The dashboard done-route parity smoke proves dashboard/API `status=done` cannot
bypass the before-done gate: weak `done` is refused, valid `done` with Receipt
Five and worker results is allowed, and bulk weak `done` is refused.

The dashboard route inventory smoke maps the inspected dashboard/API route surface:
41 dashboard/API routes, 24 mutating routes, and 24 mutating route families
covered for attachment-safety/create/delete/dependency-links/dispatch/
bulk-archive/reassign/reclaim-terminate/specify/decompose/comments/home-subscribe/board-delete/board-lifecycle/profile-routes/orchestration/`ready`/`done`, with no pending mutating dashboard/API route families in the inspected surface:

```text
validation/hermes-installed-runtime-smoke/dashboard-route-inventory-smoke.json
```

Real Hermes control-plane evidence now proves a minimal no-spawn smoke on the
live runtime: a disposable board was created, an unassigned task was created,
the task was blocked, `show --json` read back the blocked event and run record,
and the disposable board was archived through a recoverable cleanup path:

```text
validation/hermes-real-runtime-smoke/no-spawn-blocked-board-smoke.json
```

Real Hermes bounded worker-dispatch evidence now proves the next diagnostic
step on the live runtime: a disposable task was assigned to a worker profile,
the dispatcher spawned one worker, a run record and heartbeat were observed,
the task was reclaimed/blocked after timeout, cleanup was verified, and the
board was archived. This is intentionally a `BLOCKED` receipt because the
worker did not complete through the expected worker path:

```text
validation/hermes-real-runtime-smoke/real-worker-dispatch-bounded-smoke.json
```

The follow-up terminal-completion smoke studied the official Hermes worker
completion path first, then gave a disposable worker an explicit
`kanban_complete` instruction. After refreshing OpenAI Codex auth at the global
Hermes home and removing the stale local auth shadow from the
`factory-orchestrator` profile, the same route reached `done` through
`kanban_complete`:

```text
validation/hermes-real-runtime-smoke/real-worker-terminal-completion-smoke.json
```

The profile-wide live-auth matrix then created the 20 missing vFinal worker
profiles from the public worker registry without cloning `.env` or
profile-local auth, verified all 47 registry profiles exist, verified zero
registry profiles retain a local `openai-codex` auth shadow, and proved all 46
non-human profiles can answer a live `openai-codex` + `gpt-5.5` provider/model
probe:

```text
validation/hermes-real-runtime-smoke/worker-profile-live-auth-matrix-smoke.json
```

The real local-tool worker smoke then proved one bounded worker can use a real
Hermes tool beyond pure model response: `public-safety-gate` used the terminal
tool in a real workspace, ran read-only checks, returned structured metadata
and completed through `kanban_complete`:

```text
validation/hermes-real-runtime-smoke/real-worker-local-tool-quality-smoke.json
```

The worker-result ingestion smoke proves completed worker subtasks can write
worker-result artifacts back to the parent runtime directory, and parent `done`
can reconcile those artifacts without a manually supplied `worker_results_dir`.

The worker dispatch-route smoke proves the corrected dependency direction:
worker subtasks become prerequisites of the parent Factory card, the parent does
not spawn before workers finish, and spawnable worker subtasks can be claimed by
the dispatcher through a stubbed spawn function.

The worker real-process auth-block smoke proves the default dispatcher spawn
path can start a real Hermes worker process and block it safely when the
disposable profile has no provider/model credentials.

The worker route readiness preflight first proved the safe block: without
profile/config/model/provider readiness, all 23 materialized worker routes stay
blocked for production.

The worker profile readiness local-stub smoke then provisioned all 23
disposable worker profiles with explicit provider, model and local
OpenAI-compatible `/models` evidence, producing a `PASS` receipt in the
disposable runtime. This proves the factory can prepare worker routes without
touching the real Hermes runtime.

The worker dispatch-completion smoke then proved the next wiring step in the
same disposable runtime: the dispatcher claimed a materialized worker subtask,
a synthetic worker completion wrote structured Overkill metadata, and the
parent card received a worker-result ingestion event.

The worker real-process local-stub smoke then proved the stronger wiring path:
the real Hermes dispatcher spawned a real child worker process, the child saw
the `kanban_complete` tool surface, a local OpenAI-compatible streaming stub
returned a tool call, the child completed the worker task, and the parent card
received the worker-result ingestion event.

The worker real-process matrix local-stub smoke then repeated that same path
for all 23 vFinal workers. Each worker route spawned a real Hermes child
process, completed through `kanban_complete`, and produced parent ingestion in
the disposable runtime.

The dashboard dependency patch then fixed a concrete dashboard/API runtime gap:
the Kanban dashboard plugin uses FastAPI `File/Form` route parameters, so the
Hermes `web` extra must include `python-multipart`.

The service rollback drill then proved a disposable rollback-by-release-restore
path: the patched files were backed up, clean baseline files were restored,
health checks passed, a service-like process stop/start probe passed, and the
patched state was restored for later smokes.

That is not a production claim by itself. Live profile/provider model auth is
now proven across the vFinal worker registry. The local terminal-tool path,
scanner-backed specialist output quality, parent `done` reconciliation and real
gateway rollback/monitoring recovery are also proven for bounded real worker
results. vFinal still needs Operator Control Tower proof and a passing complete
update receipt before any real Hermes runtime update. A blocked update receipt
already records the current state and points at the missing Control Tower gate.

Current readiness status:

```text
docs/validation/hermes-vfinal-production-readiness-status.md
```

Production cutover packet:

```text
docs/roadmap/vfinal-production-cutover.md
```

Production loop and parallel-work rules:

```text
docs/roadmap/vfinal-production-loop.md
docs/methodology/worktrees-and-parallel-agents.md
docs/maps/overkill-factory-vfinal-mindmap.md
```

Operator Control Tower private evidence kit:

```text
docs/control-tower/operator-control-tower-private-evidence-kit.md
templates/operator-control-tower-bridge-health.json
```

Release public-safety tree gap:

```text
docs/roadmap/release-public-safety-tree-gap.md
```

The first dry pilot is complete and kept under:

```text
pilot: pilots/quasar-vault-guard-test
status: done
```

## Quick Start

Read these in order:

1. `docs/methodology/overkill-factory-vfinal.md`
2. `docs/roadmap/vfinal-production-loop.md`
3. `docs/validation/hermes-vfinal-production-readiness-status.md`
4. `docs/roadmap/vfinal-production-cutover.md`
5. `docs/methodology/worktrees-and-parallel-agents.md`
6. `docs/control-tower/operator-control-tower-private-evidence-kit.md`
7. `docs/roadmap/release-public-safety-tree-gap.md`
8. `adapters/hermes/README.md`
9. `agents/worker-roster.md`
10. `agents/worker-registry.public.json`
11. `docs/security/security-control-matrix.md`
12. `adapters/hermes/compatibility-manifest.md`
13. `docs/maps/overkill-factory-vfinal-mindmap.md`
14. `pilots/quasar-vault-guard-test/README.md`
15. `docs/roadmap/factory-11-action-plan.md`
16. `docs/methodology/factory-11-operational-hardening.md`
17. `docs/validation/heavy-validation-results.md`
18. `docs/reviews/heavy-validation-adversarial-review.md`

Run the local preflight:

```bash
python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md
python scripts/factoryctl.py gate-report --card examples/cards/v35_valid_onchain_auditor_scan.md
python scripts/factoryctl.py worker-packet --worker all --card examples/cards/v35_valid_onchain_auditor_scan.md --out examples/worker-packets/onchain-card
python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/cards/v35_valid_onchain_auditor_scan.md --out examples/worker-packets/onchain-card
python scripts/factoryctl.py validate-completion --card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md --receipt pilots/quasar-vault-guard-test/evidence/receipt-five-first-slice.json
python scripts/factoryctl.py validate-lane templates/parallel-lane-contract.json
python adapters/hermes/compatibility-check.py
python adapters/hermes/validate_v016_transition_patch.py --source-kanban-db path/to/hermes_cli/kanban_db.py
python scripts/control_tower_readonly_smoke.py
python scripts/control_tower_approval_registration_smoke.py
python scripts/operator_control_tower_proof.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python -m unittest discover -s tests -p "test_*.py" -q
```

After a specialist really runs, write structured evidence metadata:

```bash
python scripts/factoryctl.py evidence-record --worker codex-security --card examples/cards/v35_valid_security_with_scan.md --result PASS --tool codex-security:security-scan --actor security-runner --evidence-ref reports/security-scan.md
python scripts/factoryctl.py human-gate-record --card examples/cards/v35_valid_onchain_auditor_scan.md --decision approved --human-actor product-owner --evidence-ref decisions/r3-human-approval.md
```

## Current Boundaries

The repo prepares contracts and worker packets. It does not fake scanner output,
Auditor results, screenshots, independent approval, or human decisions.

The dry pilot proves the factory process and Hermes gates. It does not prove
production readiness, deploy readiness, real onchain program safety, wallet
signing, devnet/mainnet behavior, funds movement, or custody safety.

The first production-intent pilot still needs a real raw product paper.

## Public Repository Safety

Raw study material, screenshots of private sessions, private source ledgers,
local paths, private board links and internal project names do not belong in
this repository. Run `python scripts/public_safety_scan.py` before publishing or
opening a pull request.

Before publishing a branch or release tree, scan the exact committed tree too:

```bash
python scripts/public_safety_scan.py --git-ref HEAD
python scripts/public_safety_scan.py --git-ref origin/main
```

## License

MIT.
