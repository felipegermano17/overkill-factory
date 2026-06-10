# Discord Control Tower OS

Discord Control Tower OS is the owner-facing control layer for Overkill
Factory.

It makes the factory understandable and operable without turning Discord into
the source of truth.

## Decision

```text
Discord = human cockpit
Hermes or selected runtime = durable source of truth
Overkill Factory = method, gates, workers and evidence
Factory Concierge = official owner-facing voice
```

The owner creates or grants the Discord server. The factory owns everything
after that: event contracts, bridge behavior, structured approvals, health
checks, anti-spam, evidence links, and runtime registration.

## What This Layer Does

It shows:

- project status;
- current phase;
- blockers;
- pending access;
- pending approvals;
- forecast and next steps;
- forecast confidence;
- evidence links;
- release decisions;
- incident alerts;
- bot and bridge health.

It asks for:

- understanding approval;
- plan approval;
- access approval;
- budget approval;
- risk approval;
- scope-change approval;
- release approval;
- production approval.

## What This Layer Must Not Do

It must not:

- store secrets;
- replace Hermes or the selected runtime;
- approve risk on behalf of the owner;
- let free-form chat become sensitive approval;
- let specialist workers interrupt the owner by default;
- treat Discord message history as canonical evidence;
- bypass ready, done, release or human gates.

## Factory Concierge

The Factory Concierge is the owner-facing agent.

It:

- explains the state in plain language;
- consolidates worker outputs;
- asks structured questions;
- records owner decisions back into the runtime;
- protects the owner from noisy worker updates;
- makes blockers and next steps visible.

It cannot:

- approve for the owner;
- hide risk;
- invent runtime status;
- mark work complete without evidence.

## Bridge

The Discord Control Tower Bridge maps runtime events to Discord messages and
maps structured owner responses back to durable runtime events.

It must be idempotent.

Retrying an event must not duplicate approvals, blockers or worker tasks.

The bridge has no authority to mark factory work `ready`, `done`, released, or
approved by itself. It can only request that the runtime records a structured
event. The runtime and Overkill gates decide whether that event is valid.

## Minimum Contracts

The control layer uses:

- `control-tower-event.schema.json`;
- `project-projection.schema.json`;
- `approval-request.schema.json`;
- `discord-control-tower-mapping.schema.json`;
- `operator-control-tower-bridge-health.schema.json`.

The production gate also uses:

- `operator-control-tower-production-readiness.schema.json`;
- `hermes-production-proof.schema.json`.

## Rollout Order

1. Read-only status and health.
2. Project projection.
3. Blocker and forecast messages.
4. Evidence links.
5. Structured approval requests.
6. Approval response registration in the runtime.
7. Bypass and permission tests.

Structured approvals must not ship before runtime registration is proven.

The first useful milestone is not "a bot can post messages". The first useful
milestone is "the owner can see the real runtime state without the Discord layer
being able to mutate it".

The second useful milestone is "a structured owner approval can travel from
Discord back into the runtime and be rejected when the approval is malformed,
expired, sent by the wrong role, or outside the requested scope".

The public contract smoke for this rule is:

```text
validation/control-tower/control-tower-approval-registration-smoke.json
```

## Production Proof Harness

The production gate is stricter than the local contract smokes.

The local smokes prove:

- a read-only owner projection can be derived without mutating runtime state;
- a structured approval can become a runtime-registerable event;
- malformed, expired, wrong-role, unknown or scope-expanded approvals are
  rejected.

They do not prove that the owner's real Discord server, channels, roles, bridge
and runtime registration path exist.

Use the harness below after the real server/mapping exists:

```bash
python scripts/operator_control_tower_proof.py \
  --mapping /private/path/to/discord-control-tower-mapping.json \
  --runtime-registration-event /private/path/to/runtime-approval-event.json \
  --bridge-health /private/path/to/bridge-health.json
```

The `--bridge-health` file must follow
`schemas/operator-control-tower-bridge-health.schema.json`. A generic JSON file
with only `result: PASS` is not enough.

The harness also checks that the mapping and runtime approval event refer to
the same project, that the mapping contains a real board reference, that the
approval event has a real event id, and that bridge health carries non-empty
external evidence refs.

Use this public-safe helper when preparing the private evidence:

```text
docs/control-tower/operator-control-tower-private-evidence-kit.md
```

The script writes:

```text
validation/control-tower/operator-control-tower-production-readiness.json
```

If all checks pass, it also writes:

```text
validation/hermes-production-proof/operator-control-tower.json
```

The public output must stay redacted. Real Discord ids, private runtime ids,
URLs, tokens, webhooks and logs belong only in private operator evidence.

## Gate Rule

The Control Tower Gate blocks material execution from being invisible to the
owner when the work needs human tracking, approval, access, cost visibility,
material risk handling or release control.

When this layer is active, the factory needs:

- fresh project projection;
- correct approval channel;
- visible blockers;
- runtime registration path;
- bot/bridge health signal.

## Minimum Practical Server Shape

The recommended Discord setup is intentionally small:

- one dashboard channel;
- one intake channel;
- one owner-approvals channel;
- one access-requests channel;
- one blockers channel;
- one evidence-feed channel;
- one release-room channel;
- one bot-health channel;
- one project forum or thread area.

The server can become richer later, but the factory should not require a large
Discord bureaucracy to start.

## Human Setup Boundary

The only required owner-side action is to create or grant a Discord server with
the agreed channels and roles.

After that, the factory should be able to continue through:

- server mapping;
- channel mapping;
- role mapping;
- bot or webhook configuration;
- read-only projection;
- structured approval registration;
- health checks;
- negative tests.

The factory must block instead of improvising if the server, channel, role, or
runtime registration path is missing.
