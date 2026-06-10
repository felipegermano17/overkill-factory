# vFinal Production Cutover Packet

This is the public-safe cutover packet for taking Overkill Factory vFinal from
repository-hardening into real operational use.

It does not authorize a real Hermes update by itself.

## Verdict

The factory is ready for a controlled production-readiness run, but not for a
real Hermes runtime update yet.

The current real-runtime decision is:

```text
blocked
```

The blocking receipt is:

```text
validation/hermes-production-update-preflight/real-runtime-update-blocked.json
```

That receipt must become `PASS` with real proof refs before any real Hermes
runtime update.

The compatibility check currently enforces that this receipt stays `BLOCKED`
with the remaining required blockers present. When the remaining real proof
refs exist, update the preflight and its compatibility expectation together.

Production proof refs must be structured JSON evidence. Generic files or a
bare `{"result": "PASS"}` are not enough.

Use:

```text
schemas/hermes-production-proof.schema.json
templates/hermes-production-proof.json
```

The only exception is the complete Hermes update receipt, which may use:

```text
schemas/hermes-update-receipt.schema.json
adapters/hermes/update-receipt.template.json
```

## What Is Already Strong

The repository now has:

- vFinal methodology, contracts, schemas and templates;
- worker registry and worker routing for the modular factory;
- Product Experience OS and Product Face proof requirements;
- security architecture, access, autonomy, budget, dependency, eval, release
  and maturity gates;
- Control Tower contracts for owner visibility, approvals and Discord mapping;
- Hermes v0.16 candidate patches for transition gates, worker subtasks,
  dashboard/API route protection, worker-result ingestion and dependency
  direction;
- disposable installed-Hermes evidence for before-ready and before-done gates;
- dashboard/API route parity and operational-safety smokes with 0 pending
  mutating route families;
- worker route readiness, local-stub profile readiness, synthetic completion,
  real-process local-stub completion and all-worker matrix local-stub evidence;
- disposable rollback-by-release-restore drill;
- sanitized real Hermes no-spawn control-plane smoke on a disposable board;
- sanitized bounded real Hermes worker-dispatch smoke proving spawn, run record,
  heartbeat and cleanup, with completion still blocked;
- official Hermes worker-completion source study and a terminal-completion
  smoke that first exposed stale profile auth, then passed after the
  `factory-orchestrator` profile used the refreshed global OpenAI Codex auth;
- real Hermes worker-profile live-auth matrix proving all 46 non-human vFinal
  worker profiles can answer through `openai-codex` + `gpt-5.5`; the 20 missing
  profiles were created from the public worker registry without cloning `.env`
  or profile-local auth;
- real Hermes local-tool smoke proving one `public-safety-gate` worker can use
  the terminal tool in a real workspace, produce structured metadata and close
  through `kanban_complete`;
- production proof for local terminal tool authorization on that bounded real
  worker path;
- parent `done` reconciliation proof using a sanitized `public_safety_result`
  produced by the real Hermes worker;
- scanner-backed specialist-quality proof showing a real `public-safety-gate`
  worker can run the public safety and secret safety scanners and return a
  structured result;
- real Hermes gateway rollback/monitoring proof showing the systemd-managed
  gateway recovers through `Restart=always` after controlled termination and
  passes post-recovery Hermes plus Kanban health checks;
- public safety, secret safety, JSON validation and unit-test coverage.

## What Is Still Blocking Real Use

These are not paperwork items. They are production blockers.

1. Operator Control Tower proof.
2. Passing Hermes update receipt for the exact target runtime.

Until these exist, materialized worker subtasks should remain born `blocked` by
default.

The first bounded real-worker dispatch smoke did move one step past no-spawn:
the real runtime spawned a worker and heartbeat was observed. It still did not
produce a terminal worker outcome, so it confirms the blocker instead of
removing it.

The follow-up terminal-completion smoke narrowed that blocker and then closed it
for one worker profile. The first run showed that profile-local auth can shadow
fresh global auth. After the stale `factory-orchestrator` auth shadow was
removed, a profile-level live provider probe passed and the worker reached
`done` through `kanban_complete`.

The profile-wide live-auth matrix then closed the profile/model auth blocker
for the registry: all 47 vFinal profiles exist, all 46 non-human profiles pass
a live provider/model probe, and the only skipped profile is the human gate
clerk because it represents human authority. This does not prove tool
credentials, specialist output quality or parent reconciliation.

The next smoke proved a narrower but important tool loop: `public-safety-gate`
used the real terminal tool in a real workspace, ran read-only checks, returned
structured metadata and completed through `kanban_complete`. That now closes
the `real_tool_auth` production-preflight item for the local terminal-tool path,
while external tools and future card-specific auth paths remain separate
card-level proof obligations.

The sanitized real worker result was then replayed through the Overkill parent
`done` hook. The hook returned `allow_done`, so
`real_worker_done_reconciliation` is also closed for the production preflight.

A stronger public-safety specialist-quality smoke was attempted next. The first
attempt found the missing scanner command/workspace shape. The passing proof
then used a disposable public-safe workspace with the scanner scripts present:
the real worker ran both scanners, returned structured metadata and completed
through `kanban_complete`.

Production rollback/monitoring was then proven for the live Hermes gateway
path. The gateway was healthy before the test, the service was confirmed as a
systemd unit with `Restart=always`, the process was terminated under controlled
conditions, systemd recreated it, and post-recovery Hermes status plus Kanban
health checks passed. This is not a code-version rollback proof; that remains
part of the complete update receipt.

## Cutover Order

### 1. Freeze The Candidate Package

Before any real-runtime work, freeze the candidate package:

```bash
python adapters/hermes/compatibility-check.py
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python -m unittest discover -s tests -p "test_*.py" -q
```

If any command fails, stop. Do not continue into real runtime preparation.

### 2. Reconfirm Route Surface

Confirm the dashboard/API route inventory still has 0 pending mutating route
families:

```text
validation/hermes-installed-runtime-smoke/dashboard-route-inventory-smoke.json
```

If Hermes added or changed dashboard/API routes, classify the route and add
parity or operational-safety proof before continuing.

### 3. Prepare A Disposable Runtime With Realistic Profiles

Use a disposable Hermes checkout and disposable Hermes home.

Do not use the real production Hermes home for this stage.

The disposable runtime must have:

- one bounded worker profile using a non-stub model endpoint;
- only the minimum tools/auth needed for the proof;
- explicit cost and cleanup boundaries;
- isolated board/task data;
- rollback path already known before the test starts.

### 4. Run One Real Worker Proof

Run one materialized vFinal worker subtask end to end.

The proof must show:

- the worker was spawned by the normal dispatcher path;
- the model endpoint was not a local deterministic stub;
- required tools/auth were available and used safely;
- the worker completed through `kanban_complete` or blocked through
  `kanban_block`;
- the worker result included structured metadata and evidence refs;
- the parent task ingested the worker result.

Conversational success is not enough.

### 5. Reconcile Parent Done

Status: done for the bounded `public-safety-gate` proof.

The real worker result already proved parent `done` reconciliation in:

```text
validation/hermes-production-proof/real-worker-done-reconciliation.json
```

The parent may close only when Receipt Five and required worker evidence agree.

The next blocker is not reconciliation or rollback anymore; it is the
operator-facing Control Tower proof and the passing complete update receipt.

### 6. Record Production Rollback And Monitoring

Status: done for the live gateway recovery path.

The current proof covers:

- systemd-managed gateway recovery through `Restart=always`;
- health checks after recovery;
- public-safe evidence without raw runtime ids, paths or logs.

Disposable rollback-by-release-restore is already proven, but it is not enough
for production by itself. The complete update receipt must still carry the
package/code rollback plan, monitoring owner, rollback trigger and post-update
success check.

### 7. Prove Operator Control Tower

The owner-facing layer must prove:

- real runtime state can be projected into owner-visible status;
- blockers, forecasts and evidence links are visible;
- structured approvals can be registered back into runtime events;
- malformed, expired, wrong-role or scope-expanded approvals are rejected;
- bot/bridge health is visible and follows
  `schemas/operator-control-tower-bridge-health.schema.json`;
- Discord does not become the source of truth.

If the Discord server is not ready, the production update remains blocked.

The executable harness is:

```bash
python scripts/operator_control_tower_proof.py \
  --mapping /private/path/to/discord-control-tower-mapping.json \
  --runtime-registration-event /private/path/to/runtime-approval-event.json \
  --bridge-health /private/path/to/bridge-health.json
```

`bridge-health.json` must be a real bridge-health receipt, not a generic
`result: PASS` placeholder.

Current state is intentionally blocked in:

```text
validation/control-tower/operator-control-tower-production-readiness.json
```

### 8. Produce The Complete Update Receipt

Create the update receipt for the exact target runtime:

```text
adapters/hermes/update-receipt.template.json
```

The current blocked receipt is:

```text
validation/hermes-production-update-preflight/current-update-receipt-blocked.json
```

It must name the before/after runtime, patch result, checks, proof refs,
rollback plan, risk owner and real-runtime decision.

### 9. Run The Production Update Preflight

Run the preflight with all real proof refs:

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

If the result is not `PASS`, stop.

The preflight checks that each proof:

- is JSON;
- has the correct `record_type`;
- matches the expected proof type;
- has `result: PASS`;
- has non-empty evidence refs;
- has stated limits;
- is not itself declaring a blocked real-runtime decision.

### 10. Request Explicit Operator Gate

Even after preflight `PASS`, the update still needs explicit operator approval.

The approval must name:

- runtime target;
- rollback owner;
- risk owner;
- monitoring owner;
- update window;
- post-update success check;
- rollback trigger.

## First Production-Readiness Run Shape

The first serious run should be intentionally small.

Use one bounded vFinal card with:

- no broad credentials;
- no irreversible deployment;
- one worker route selected for real proof;
- clear done definition;
- explicit rollback;
- human-visible Control Tower projection.

The goal is not to ship a big product. The goal is to prove that the factory can
move from plan to worker execution to evidence to owner visibility without
lying to itself.

The first real runtime control-plane smoke is already complete:

```text
validation/hermes-real-runtime-smoke/no-spawn-blocked-board-smoke.json
```

It proves real board/task/block/readback/archive behavior only. The next real
runtime diagnostic checkpoint is:

```text
validation/hermes-real-runtime-smoke/real-worker-dispatch-bounded-smoke.json
```

It proves real worker spawn, run-record creation, heartbeat and cleanup, but
not terminal completion. The follow-up proof closes that single-profile gap:
one bounded worker route finished through `kanban_complete` with non-stub
execution.

The first terminal-completion diagnostic is also recorded:

```text
validation/hermes-real-runtime-smoke/real-worker-terminal-completion-smoke.json
```

It proves the official Hermes worker-completion docs were studied, the worker
profile passed a live provider/model probe, the worker was explicitly instructed
to call `kanban_complete`, and the runtime reached `done` through that tool.

Use the diagnostic runbook for that exact blocker:

```text
docs/roadmap/real-worker-completion-diagnostic.md
```

That diagnostic must start by studying the official Hermes documentation for
worker completion, blocking, heartbeat, reclaim, run records, profile/model
configuration and cleanup behavior. Runtime experiments without this source
pass are not enough.

## Stop Conditions

Stop immediately if:

- a worker can spawn without required profile readiness;
- a parent card can close before required worker evidence exists;
- dashboard/API can bypass a gate;
- Discord approval can bypass runtime validation;
- a receipt contains local paths, private board links or private runtime ids;
- gateway recovery proof or package rollback plan is missing;
- production update preflight is `BLOCKED`;
- the operator gate is missing.

## Handoff Summary

The next useful production step is:

```text
Operator Control Tower proof
```

The next owner-side dependency is:

```text
Discord server or equivalent Control Tower surface ready for mapping
```

The real Hermes runtime remains untouched until the preflight and operator gate
both pass.
