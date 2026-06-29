# Runtime and state

Overkill Factory separates runtime from method.

This separation is one of the most important ideas in the system.

## Hermes is the runtime

Hermes owns the durable work floor:

- boards;
- cards;
- dependencies;
- statuses;
- typed blockers;
- dispatch;
- worker tasks;
- logs;
- comments;
- run state.

If the next action exists only in a chat message, it is fragile. If it exists in Hermes state, it can be resumed, inspected and repaired.

## The factory is the method

The factory owns the production rules:

- source boundary;
- product definition / PRD;
- method selection;
- risk route;
- capability route;
- worker packet format;
- gate rules;
- evidence requirements;
- review policy;
- human-gate policy;
- release policy;
- Receipt Five.

The factory should not replace Hermes. It should use Hermes as the runtime and fail closed when work tries to bypass it.

## Why this matters

Without separation, an agent can act like the factory just by speaking confidently.

That is not acceptable.

Official factory work should be backed by durable state and contracts. A worker result should connect to a packet, a card, evidence and a parent requirement. A release should connect to gates, review and Receipt Five. A human decision should connect to a decision package, not a vague prompt.

## State categories

A healthy run separates these categories:

- source state: what was provided and what was inferred;
- product state: PRD/product definition and coverage;
- runtime state: cards, dependencies, dispatch and worker runs;
- evidence state: artifacts, tests, screenshots, scans, reviews;
- decision state: human gates, approvals, blocks and risk acceptance;
- closure state: Receipt Five and release/block/operate/learnback outcome.

When those categories mix, the system becomes hard to trust.

## Fail-closed behavior

The factory should fail closed when state is missing.

Examples:

- no product definition: do not pretend the target is clear;
- packet but no result: do not claim execution;
- result but no evidence: do not close;
- release without owner/rollback/monitoring: do not promote;
- human decision required: do not auto-approve;
- local proof only: do not call it live proof.
