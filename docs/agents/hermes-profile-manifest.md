# Hermes Profile Manifest

This manifest defines what counts as an executable Hermes profile for the
factory. A worker profile is not complete until the runtime profile can be
inspected and smoke-tested against its worker packet.

## Required Runtime Pieces

Each Hermes-bound worker must have:

- profile name matching `hermes_profile_name`;
- profile description derived from the public worker profile mission;
- `SOUL.md` containing identity, mission, authority, refusal rules, evidence,
  review, handoff and failure policy;
- the `overkill-factory` skill available;
- the `hermes-kanban` skill available;
- every additional `skill_refs` entry either installed or explicitly mapped to
  a runtime capability;
- least-privilege tool policy;
- no direct card-state mutation authority;
- smoke evidence proving the profile can receive a bounded worker packet and
  answer in the expected format.

For builders, the smoke must prove more than profile presence: the generated
worker packet must expose the correct receipt field, queue class, skill refs
and refusal boundaries for that builder's surface. A frontend builder without
Product Face handoff, or a Solana builder without Quasar/Auditor boundaries, is
not considered operable.

## Source Of Truth

The runtime profile does not decide its own queue. Runtime queue is computed by
`factoryctl.worker_queue_class` and exposed on `worker_task.queue_class`.

The profile binding may describe queue policy, but it is not an execution
source. This avoids split-brain behavior between Hermes routing and factory
transition planning.

## Result Schema Rule

The result schema in `agents/hermes-profile-bindings.public.json` must match the
result emitted by the worker result builder:

- generic workers use `schemas/worker-result.schema.json`;
- surface builders use `schemas/worker-result.schema.json` with their specific
  receipt field, such as `frontend_build_result`,
  `backend_api_build_result`, `solana_quasar_build_result` or
  `agent_runtime_result`;
- Product Face uses `schemas/product-face-result.schema.json`;
- Solana/Quasar Auditor uses `schemas/auditor-result.schema.json`;
- human decisions use `schemas/human-gate-record.schema.json`.

If the schema promised by the binding and the schema emitted by the result
record differ, the worker result is invalid.

## Smoke Rule

A profile smoke is public-safe evidence that records:

- worker id;
- profile name;
- profile files present;
- skills expected;
- queue source;
- result schema;
- command or adapter path used;
- response shape;
- pass/fail status.

Smoke evidence is not product approval. It proves the agent profile is
operable. Product evidence still belongs to the product card.

## Builder Routing Rule

`implementation-worker` is a fallback. It must not be called when a card has a
surface owned by a specialist builder. `scripts/factoryctl.py` owns this route:

- frontend/mobile/wallet UI -> `frontend-builder`;
- backend/API/auth -> `backend-api-builder`;
- data/schema/migration -> `data-persistence-builder`;
- Solana/Quasar/onchain -> `solana-quasar-builder`;
- onchain QA/devnet/compute units -> `solana-quasar-qa-engineer`;
- wallet/signing/transaction -> `wallet-transaction-builder`;
- integration/fullstack/E2E -> `integration-builder`;
- tests/evals/regression -> `test-automation-builder`;
- infra/runtime/deploy -> `infra-devops-builder`;
- Hermes/factory/agent/skill/MCP -> `agent-runtime-builder`.

This is the main anti-theater rule for execution. A broad developer profile can
exist only as a safe fallback, not as the owner of every implementation card.
