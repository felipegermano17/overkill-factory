# Real Worker Completion Diagnostic

This is the public-safe diagnostic record for the real Hermes worker-completion
blocker that was found and then closed.

The real runtime has already proven disposable board/task control-plane
behavior, worker spawn, run-record creation, heartbeat and cleanup. It has now
also proven one real terminal worker completion and profile-wide live
provider/model auth for every non-human vFinal worker profile.

## Closed Blocker

The original blocker was: the factory was not production-ready until one
bounded worker route reached a terminal runtime outcome by itself:

- success through `kanban_complete`; or
- honest block through `kanban_block`.

A worker that spawns and heartbeats but never closes is useful evidence, but it
is not release evidence.

That specific blocker is now closed for `factory-orchestrator`: the worker used
the live provider/model path and reached `done` through `kanban_complete`.
Profile/model auth is also closed across the vFinal registry: all 46 non-human
worker profiles passed a live `openai-codex` + `gpt-5.5` probe.

The current blockers are now Control Tower proof and turning the blocked update
receipt into a passing final update receipt. Local terminal-tool auth,
scanner-backed specialist output quality, parent `done` reconciliation and real
gateway rollback/monitoring are proven for bounded real worker results.

## Diagnostic Goal

Produce one sanitized receipt proving either:

- the worker completed with structured metadata and evidence refs; or
- the worker blocked itself with a clear machine-readable reason.

The receipt must not include raw runtime ids, private paths, board names,
secrets, provider tokens, screenshots of private state or raw logs.

## Current Finding

The first explicit terminal-completion smoke was blocked before the Kanban tool
protocol started.

The worker profile existed and had the Kanban worker skill, but its local auth
state shadowed the refreshed global auth state. Status-level checks were
misleading: the worker still failed a live provider request before it could call
`kanban_show`, `kanban_complete` or `kanban_block`.

The auth issue was then fixed for `factory-orchestrator`: OpenAI Codex auth was
refreshed at the global Hermes home, the stale local profile auth shadow was
removed, a profile-level provider/model probe passed, and the same disposable
worker route reached `done` through `kanban_complete`.

The profile-wide follow-up created the 20 missing vFinal worker profiles from
the public worker registry without cloning `.env` or profile-local auth. After
that, all 47 registry profiles existed, zero registry profiles retained a local
`openai-codex` auth shadow, and all 46 non-human profiles passed a live
provider/model probe.

This creates a new preflight rule:

```text
status-level auth is not enough; every worker profile provider route needs a live probe
```

The factory must not treat a worker route as production-ready just because a
local status command says the provider is logged in.

## Before Touching The Real Runtime

Study the official Hermes documentation before dispatching the next real worker.

The study must answer, in plain language:

- how Hermes expects a worker to finish work;
- which tool or event path is canonical for `kanban_complete`;
- which tool or event path is canonical for `kanban_block`;
- how dispatcher heartbeat, timeout, reclaim and run records are supposed to
  behave;
- which profile, model and tool configuration fields are required for a normal
  non-stub worker route;
- what the official docs say about safe cleanup and recovery after a stuck
  worker.

Record only a public-safe summary in this repository. Do not paste raw private
runtime output, internal paths, board ids, task ids, secrets or private logs.

Run the repository preflight:

```bash
python adapters/hermes/compatibility-check.py
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python -m unittest discover -s tests -p "test_*.py" -q
```

Stop if any command fails.

Confirm the current baseline receipts:

```text
validation/hermes-real-runtime-smoke/no-spawn-blocked-board-smoke.json
validation/hermes-real-runtime-smoke/real-worker-dispatch-bounded-smoke.json
validation/hermes-real-runtime-smoke/real-worker-terminal-completion-smoke.json
validation/hermes-real-runtime-smoke/worker-profile-live-auth-matrix-smoke.json
validation/hermes-production-update-preflight/real-runtime-update-blocked.json
```

The preflight receipt must remain `BLOCKED` until the diagnostic produces real
completion evidence.

## Disposable Runtime Shape

Use a disposable board and one disposable task.

The task must have:

- one worker profile;
- a live provider/model probe that passes for the exact worker profile before dispatch;
- a bounded runtime window;
- a clear instruction to call `kanban_complete` or `kanban_block`;
- no broad credentials;
- no production deployment authority;
- no destructive action authority;
- cleanup planned before dispatch.

## What To Inspect If The Worker Does Not Close

Inspect only enough runtime detail to classify the failure. Do not store raw
runtime output in the public repository.

Classify the blocker as one of these:

- provider status says logged in but live request is rejected;
- provider or model not reachable;
- model reachable but tool surface missing;
- tool surface present but worker instruction does not force terminal closure;
- worker profile missing required environment or runtime config;
- worker process crashes before tool call;
- worker stays alive but never chooses a terminal tool call;
- dispatcher/run bookkeeping prevents completion ingestion;
- timeout too short for the selected model/tool path;
- unknown, needs deeper private runtime investigation.

## PASS Criteria

A real worker completion proof may become `PASS` only when all are true:

- read-only runtime status was checked first;
- disposable board and task were created;
- worker was dispatched through the normal runtime path;
- worker profile used a non-stub model endpoint;
- profile/provider live auth probe passed before dispatch;
- required tool surface was visible to the worker;
- worker called `kanban_complete` or `kanban_block`;
- runtime state reached the matching terminal status;
- structured worker metadata was recorded;
- evidence refs were present and sanitized;
- cleanup was verified;
- original runtime pointer/state was not unintentionally changed.

## BLOCKED Criteria

Record `BLOCKED`, not `PASS`, when:

- the worker spawns but does not close;
- provider status says logged in but a live request is rejected;
- the model endpoint is missing or unreachable;
- the tool surface is absent;
- the worker output is conversational but not a runtime terminal event;
- cleanup is incomplete or unverified;
- evidence is not sanitized enough for the public repository.

## After The Diagnostic

Update these artifacts:

```text
validation/hermes-real-runtime-smoke/
docs/validation/hermes-vfinal-production-readiness-status.md
docs/roadmap/vfinal-production-cutover.md
adapters/hermes/compatibility-manifest.md
```

Then rerun:

```bash
python adapters/hermes/compatibility-check.py
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python -m unittest discover -s tests -p "test_*.py" -q
```

Do not change the production update preflight from `BLOCKED` to `PASS` until
the worker completion receipt and all other production-only proofs exist.
