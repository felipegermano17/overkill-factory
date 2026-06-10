# Factory vFinal Upgrade Plan

This document is a public-safe implementation plan.

It does not copy private research notes, private product context, local paths,
internal board ids, or raw source captures.

## Short Verdict

Factory 11 hardened the existing production line.

Factory vFinal turns that line into a modular agentic software factory.

The next implementation step is not a real product pilot. The next step is to
materialize the vFinal contracts, workers, gates, templates, skill guidance,
examples, and validation hooks in this repository.

## Current Baseline

The repository already has useful Factory 11 pieces:

- public safety scan;
- CI;
- Hermes compatibility notes;
- worker registry;
- worker contract schema;
- security control matrix;
- Product Face proof;
- context spine;
- operational hardening notes;
- `factoryctl.py` preflight and worker packet helpers.

These pieces should be reused.

The gap is that the repository still speaks mostly in the Factory 11 / v3.6
model. It does not yet encode the full vFinal model.

## Implementation Progress

Initial vFinal materialization has started:

- public vFinal methodology added;
- central schemas accept `OVERKILL_VFINAL`;
- vFinal schemas and templates added for outcome, method, software development,
  product experience, data/metrics, agent eval, dependency, security
  architecture, access, autonomy readiness, privacy/compliance, budget,
  production readiness, incident/support, legacy/migration, platform/DevEx,
  user docs/onboarding, loop plan, completion audit and factory maturity;
- worker registry includes vFinal workers;
- owner interface and control tower are now part of the public-safe vFinal
  method;
- Control Tower schemas/templates exist for project projection, approval
  request, event emission and Discord mapping;
- worker registry includes the Factory Concierge, Discord Control Tower Bridge
  and Control Tower Projection Worker;
- `factoryctl.py` routes Control Tower workers when owner interface, Discord,
  forecast or approval surfaces are required;
- a public-safe validation card proves Control Tower workers are required and
  blocked when projection, event, approval request and Discord mapping are
  missing;
- `validation/control-tower/control-tower-readonly-smoke.json` proves a
  public-safe read-only Control Tower path: runtime-shaped state produces a
  project projection, owner event, pending approval request and redacted
  Discord mapping without mutating runtime state or claiming Discord authority;
- `validation/control-tower/control-tower-approval-registration-smoke.json`
  proves the structured approval contract rejects wrong role, expired request,
  scope expansion, unknown approval id and ambiguous decision, and only emits a
  runtime-registerable approval event for a matching scoped owner decision;
- local tests, public JSON validation, public safety, secret safety, Hermes
  vFinal smoke, compatibility check and local remote-proof smoke pass after the
  Control Tower materialization;
- `factoryctl.py` routes and blocks essential vFinal gates;
- validation cards cover missing access/security and a ready R3 vFinal path;
- Hermes adapter local vFinal smoke passes;
- local clean proof passes;
- local tests, compatibility check, public JSON validation, public safety scan,
  and secret safety scan pass.
- a private disposable Hermes Kanban smoke proved the live board/task/comment/
  complete/readback path without publishing internal runtime IDs.
- the Kanban event bridge can adapt Hermes task JSON into the vFinal transition
  hook in local tests.
- a private disposable Hermes task JSON bridge smoke proved live Kanban task
  payload -> bridge -> transition hook -> worker ledger without worker spawn.
- a public-safe disposable adapter runtime smoke now proves before-ready
  routing, idempotent retry, before-ready blocking, Control Tower blocking,
  before-done missing-result blocking, before-done `allow_done` with valid
  worker results, and Kanban task JSON bridge parity at the hook layer.
- a public Hermes v0.16 candidate patch now wires the vFinal Kanban transition
  gate into direct `ready` creation, automatic ready recompute, manual
  `promote_task`, `unblock_task` to `ready` and `complete_task` paths.
- `validation/hermes-v016-transition-patch/patch-apply-receipt.json` proves the
  candidate patch is public-safe, applies to a clean Hermes v0.16
  `kanban_db.py`, and compiles.
- `validation/hermes-installed-runtime-smoke/installed-runtime-smoke.json`
  proves the patch in a disposable installed-Hermes CLI/Kanban runtime for
  direct `ready` creation blocking, positive `ready` allowance with worker
  ledger creation, weak `done` blocking, positive `done` allowance with Receipt
  Five plus worker results, manual unblock-to-ready blocking and automatic
  recompute-to-ready blocking. It also proves patch reversal rollback in the
  disposable runtime.
- `validation/hermes-installed-runtime-smoke/worker-subtasks-smoke.json` proves
  patches `0002` and `0003` can materialize 23 real Hermes worker subtasks from
  a fresh vFinal `ready` card, link them to the parent and keep them blocked as
  the default no-spawn state.
- `validation/hermes-installed-runtime-smoke/worker-subtasks-idempotency-smoke.json`
  proves a second CLI gate pass through `block -> unblock` reuses the same 23
  worker subtasks instead of duplicating child links.
- `validation/hermes-installed-runtime-smoke/dashboard-route-parity-smoke.json`
  proves dashboard/API `status=ready` and bulk `status=ready` now use the vFinal
  gate instead of direct `ready` writes.
- `validation/hermes-installed-runtime-smoke/dashboard-create-route-parity-smoke.json`
  proves dashboard/API `POST /tasks` does not expose a `status` field, blocks
  weak direct ready creation, and allows valid direct ready creation with 23
  blocked worker subtasks.
- `validation/hermes-installed-runtime-smoke/dashboard-dispatch-route-parity-smoke.json`
  proves dashboard/API `POST /dispatch` does not spawn blocked worker subtasks,
  does not spawn the parent Factory card while worker prerequisites are open,
  and can spawn one selected ready worker through a stubbed spawn function.
- `validation/hermes-installed-runtime-smoke/worker-result-ingestion-smoke.json`
  proves completed worker subtasks can write worker-result artifacts to the
  parent runtime directory, and parent `done` can reconcile them without a
  manually supplied `worker_results_dir`.
- `validation/hermes-installed-runtime-smoke/worker-dispatch-route-smoke.json`
  proves patch `0006` fixes dependency direction, the parent Factory card waits
  on unfinished worker subtasks, and spawnable materialized workers can be
  claimed by the dispatcher through a stubbed spawn function.
- `validation/hermes-installed-runtime-smoke/worker-real-process-auth-block-smoke.json`
  proves the default dispatcher spawn path starts a real Hermes worker process
  and blocks safely when the disposable profile has no provider/model
  credentials.
- `validation/hermes-installed-runtime-smoke/worker-route-readiness-blocked.json`
  proves the current disposable worker route is still production-blocked:
  23/23 materialized worker profiles need explicit profile/config/model/provider
  readiness before worker subtasks may be born `ready`.
- `validation/hermes-installed-runtime-smoke/worker-profile-readiness-local-stub-smoke.json`
  proves all 23 disposable worker profiles can be provisioned with explicit
  provider, model and local OpenAI-compatible `/models` evidence and pass the
  worker-route readiness preflight in a disposable runtime.
- `validation/hermes-installed-runtime-smoke/worker-dispatch-completion-smoke.json`
  proves the dispatcher can claim one materialized worker subtask, a synthetic
  worker completion can write structured Overkill metadata, and the parent card
  receives worker-result ingestion evidence.
- `validation/hermes-installed-runtime-smoke/worker-real-process-local-stub-smoke.json`
  proves the real dispatcher can spawn one real Hermes child worker process, the
  child can see the `kanban_complete` tool surface, a local OpenAI-compatible
  streaming stub can return the tool call, and the parent receives
  worker-result ingestion evidence.
- `validation/hermes-installed-runtime-smoke/worker-real-process-matrix-local-stub-smoke.json`
  repeats that proof for all 23 vFinal workers.
- `validation/hermes-v016-transition-patch/dashboard-dependency-patch-apply-receipt.json`
  proves patch `0007` adds the missing `python-multipart` dependency to the
  Hermes `web` extra.
- `validation/hermes-installed-runtime-smoke/dashboard-delete-route-guard-smoke.json`
  proves dashboard/API `DELETE /tasks/{task_id}` blocks destructive delete for
  vFinal parent cards and worker subtasks while preserving normal disposable
  task deletion.
- `validation/hermes-installed-runtime-smoke/dashboard-links-route-guard-smoke.json`
  proves dashboard/API `POST /links` and `DELETE /links` block manual dependency
  edits that touch vFinal parent cards or worker subtasks while preserving
  ordinary disposable task links.
- `validation/hermes-installed-runtime-smoke/dashboard-attachment-route-safety-smoke.json`
  proves dashboard/API attachment safety: traversal filenames are sanitized
  under the board attachment root, ordinary attachment delete works, and
  tampered outside-root delete is blocked.
- `validation/hermes-installed-runtime-smoke/dashboard-bulk-archive-guard-smoke.json`
  proves dashboard/API `POST /tasks/bulk` with `archive=True` blocks vFinal
  parent cards and worker subtasks while preserving ordinary disposable task
  archive.
- `validation/hermes-installed-runtime-smoke/dashboard-reassign-route-guard-smoke.json`
  proves dashboard/API `POST /tasks/{task_id}/reassign` blocks manual execution
  profile changes for vFinal parent cards and worker subtasks while preserving
  ordinary disposable task reassign.
- `validation/hermes-installed-runtime-smoke/dashboard-reclaim-terminate-guard-smoke.json`
  proves dashboard/API `POST /tasks/{task_id}/reclaim` and
  `POST /runs/{run_id}/terminate` block generic recovery controls for vFinal
  worker subtasks while preserving ordinary disposable task recovery.
- `validation/hermes-installed-runtime-smoke/dashboard-specify-route-guard-smoke.json`
  proves dashboard/API `POST /tasks/{task_id}/specify` blocks generic auxiliary
  rewrite/promotion for vFinal parent cards and worker subtasks while
  preserving ordinary disposable task specify.
- `validation/hermes-installed-runtime-smoke/dashboard-decompose-route-guard-smoke.json`
  proves dashboard/API `POST /tasks/{task_id}/decompose` blocks generic
  auxiliary task-graph fan-out for vFinal parent cards and worker subtasks
  while preserving ordinary disposable task decompose.
- `validation/hermes-installed-runtime-smoke/dashboard-comments-route-append-only-smoke.json`
  proves dashboard/API `POST /tasks/{task_id}/comments` stays available for
  operator notes on vFinal parent cards and worker subtasks, but only appends
  comment/event rows and does not change task contract state.
- `validation/hermes-installed-runtime-smoke/dashboard-home-subscribe-route-visibility-smoke.json`
  proves dashboard/API `POST /tasks/{task_id}/home-subscribe/{platform}` and
  `DELETE /tasks/{task_id}/home-subscribe/{platform}` only add/remove
  notification rows for owner visibility and do not change task contract state.
- `validation/hermes-installed-runtime-smoke/dashboard-board-delete-route-guard-smoke.json`
  proves dashboard/API `DELETE /boards/{slug}` blocks archive and hard-delete
  for boards containing vFinal parent cards or worker subtasks while preserving
  ordinary disposable board archive/delete.
- `validation/hermes-installed-runtime-smoke/dashboard-board-lifecycle-operational-safety-smoke.json`
  proves dashboard/API `POST /boards`, `PATCH /boards/{slug}` and
  `POST /boards/{slug}/switch` only create board metadata, update display
  metadata or change current-board selection, without mutating existing vFinal
  task graphs.
- `validation/hermes-installed-runtime-smoke/dashboard-profile-routes-operational-safety-smoke.json`
  proves dashboard/API `PATCH /profiles/{profile_name}` and
  `POST /profiles/{profile_name}/describe-auto` only update profile metadata.
  The auto-description success path is stubbed locally and does not claim real
  auxiliary model quality.
- `validation/hermes-installed-runtime-smoke/dashboard-orchestration-route-operational-safety-smoke.json`
  proves dashboard/API `PUT /orchestration` only updates Kanban orchestration
  config knobs, rejects missing profile overrides before save, persists valid
  settings, clears overrides and does not mutate existing vFinal task graphs.
- `validation/hermes-installed-runtime-smoke/dashboard-done-route-parity-smoke.json`
  proves dashboard/API `status=done` and bulk `status=done` respect the
  before-done gate.
- `validation/hermes-installed-runtime-smoke/dashboard-route-inventory-smoke.json`
  maps the dashboard/API route surface: 41 total routes, 24 mutating routes, 24
  mutating route families covered for attachment-safety/create/delete/
  dependency-links/dispatch/bulk-archive/reassign/reclaim-terminate/specify/decompose/comments/home-subscribe/board-delete/board-lifecycle/profile-routes/orchestration/`ready`/`done`,
  with no pending mutating dashboard/API route families in the inspected
  surface.
- `validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json`
  proves disposable rollback-by-release-restore choreography with baseline
  restore, health checks, service-like stop/start and patched-state
  restoration.

Still pending:

- any future dashboard/API route additions, which must go through inventory and
  parity or operational-safety proof before real runtime update;
- real tool-auth proof for materialized worker subtasks;
- production service-manager rollback/monitoring proof;
- real autonomous specialist output quality;
- live structured approval registration from the owner interface back into
  Hermes or the selected runtime;
- live evidence reconciliation before any production claim.

The operational sequence for those remaining items is captured in:

```text
docs/roadmap/vfinal-production-cutover.md
```

## vFinal Additions

The upgrade must add these first-class areas:

- Product Outcome and Discovery;
- Agentic Method Router;
- Software Development OS;
- Product Experience OS;
- Data, Metrics and Analytics;
- Agent Quality and Evals;
- Production Operations;
- Dependency and Integration;
- Access and Capability;
- Autonomy Readiness;
- Security Architecture;
- Compliance, Privacy and Legal;
- Budget and Cost Control;
- Factory Maturity Audit.
- Owner Interface and Control Tower.

## Implementation Order

### 1. Public Methodology

Add `docs/methodology/overkill-factory-vfinal.md`.

It should explain the vFinal journey in plain language:

```text
source -> outcome/discovery -> Product SOT -> method -> plans -> gates
-> autonomy readiness -> execution -> proof -> review -> production -> learnback
-> maturity audit
```

Factory 11 should remain documented as the previous hardening baseline, not as
the final model.

### 2. Contracts And Schemas

Update or add schemas for:

- factory card vFinal;
- outcome contract;
- discovery brief;
- method contract;
- security architecture plan;
- access and capability checklist;
- autonomy readiness packet;
- metrics plan;
- agent eval plan;
- production readiness plan;
- budget contract;
- factory maturity scorecard;
- worker packet;
- worker result;
- gate report;
- completion audit.

### 3. Templates

Add simple templates for the new contracts.

Templates must be usable by agents without reading private chat history.

### 4. Workers And Gates

Update the public worker registry and `factoryctl.py` so the factory can route
and block work using the vFinal model.

New or upgraded workers should cover:

- outcome and discovery;
- method routing;
- software planning;
- product experience routing;
- data and metrics;
- agent evals;
- dependency integration;
- access and capability;
- security architecture;
- privacy and compliance;
- budget and cost;
- production readiness;
- incident and support;
- legacy migration;
- platform and DevEx;
- user docs and onboarding;
- factory maturity audit.

### 5. Skill And Runtime Adapter

Update the Codex skill and Hermes adapter docs so agents follow vFinal by
default.

Local preflight scripts are not final validation. Real runtime validation needs
Kanban state, run logs, gate reports, worker packets, receipts, and evidence
reconciliation.

Treat `dispatch --dry-run` as disposable-board-only evidence. It may report
planned spawns and can still leave transition evidence in the card history, so
it must not be considered a zero-mutation read-only operation on an important
board.

### 5.1 Owner Interface And Control Tower

Add public-safe contracts and guidance for the owner-facing control layer.

The recommended front is Discord, but the durable state remains in Hermes or
the selected runtime.

Required artifacts:

- control tower event schema/template;
- project projection schema/template;
- approval request schema/template;
- Discord mapping schema/template;
- Factory Concierge worker registry entry;
- Discord Control Tower Bridge worker registry entry;
- Control Tower Projection Worker registry entry.

The first implementation must be read-only: status, blockers, forecast,
evidence links and health alerts. Structured approvals come only after runtime
gate decisions can be registered back into Hermes.

### 6. Examples And Tests

Add examples for:

- a simple low-risk task;
- a product with a visible interface;
- a high-risk task blocked by missing access;
- a high-risk task blocked by missing security architecture;
- a high-risk task with valid gates and evidence.
- an owner-facing project projection;
- a structured approval request.

Tests should prove that simple work stays lightweight and high-risk work cannot
skip required gates.

### 7. Validation

The upgrade is not complete until:

- schema tests pass;
- `factoryctl.py` tests pass;
- public safety scan passes;
- secret safety scan passes when available;
- a disposable adapter smoke validates vFinal transitions;
- a disposable installed-Hermes smoke validates the same transitions through
  real CLI/Kanban state;
- a disposable installed-Hermes smoke validates real blocked worker-subtask
  materialization from the vFinal worker ledger;
- a disposable installed-Hermes smoke validates worker-subtask idempotency for a
  second CLI gate pass;
- dashboard/API `ready` route parity is proven;
- worker-result ingestion from completed subtasks is proven;
- worker-route readiness blocks unsafe production dispatch and later passes in
  a disposable local-stub profile-readiness smoke;
- dispatcher claim, synthetic worker completion and parent ingestion pass in a
  disposable installed-Hermes smoke;
- real-process local-stub worker completion passes through `kanban_complete`
  and parent ingestion;
- real-process matrix local-stub worker completion passes for all 23 vFinal
  workers;
- dashboard dependency patch `0007` is applied before dashboard/API parity
  smokes;
- dashboard/API `POST /tasks` create-route parity is proven;
- dashboard/API `POST /dispatch` dispatch-route mechanics are proven;
- dashboard/API `DELETE /tasks/{task_id}` hard-delete protection is proven;
- dashboard/API `POST /links` and `DELETE /links` dependency protection is
  proven;
- dashboard/API attachment upload/delete safety is proven;
- dashboard/API bulk archive protection is proven;
- dashboard/API reassign protection is proven;
- dashboard/API reclaim/terminate protection is proven;
- dashboard/API specify protection is proven;
- dashboard/API decompose protection is proven;
- dashboard/API comments append-only behavior is proven;
- dashboard/API home-subscribe visibility-only behavior is proven;
- dashboard/API board archive/delete protection is proven;
- dashboard/API board lifecycle operational safety is proven;
- dashboard/API profile route operational safety is proven;
- dashboard/API orchestration route operational safety is proven;
- dashboard/API `done` route parity is proven;
- dashboard/API route inventory is generated with 0 pending mutating route
  families, and compatibility checks enforce that zero-pending state;
- disposable rollback-by-release-restore drill passes with baseline restore,
  health checks, service-like stop/start and patched-state restoration;
- non-stub profile/model execution is proven;
- patch reversal rollback is proven in the disposable installed runtime;
- production service-manager rollback/monitoring proof is complete before any
  real runtime update;
- Control Tower read-only projection is derived from runtime state;
- structured approval contracts reject malformed decisions before live
  registration;
- structured approvals are registered in the runtime before they affect gates;
- at least one live validation produces reconciled evidence.

## Non-Goals

Do not run a serious product pilot before contracts and gates are materialized.

Do not claim production readiness from local script output alone.

Do not put private product names, local paths, internal ids, personal identities,
private runtime details, or raw study extracts into this repository.

Do not turn every small task into a heavy R4 process.

Do not let Discord or any owner interface become a parallel source of truth.

## Done Definition

Factory vFinal is materialized when this repository can operate the vFinal
journey without relying on private context:

- public methodology exists;
- schemas and templates exist;
- worker registry knows the vFinal workers;
- `factoryctl.py` validates vFinal cards and gates;
- skill guidance matches vFinal;
- examples and tests cover the important paths;
- Control Tower contracts exist for status, forecast, approvals and mapping;
- public safety passes;
- runtime smoke evidence exists;
- worker-subtask materialization evidence exists;
- live evidence is reconciled before any production claim.
