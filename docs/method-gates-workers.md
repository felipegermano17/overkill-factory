# Method, gates and workers

The factory separates method, gates and workers so no single agent can become the whole factory.

## Method

The method is the chosen process for the work.

Examples:

- spec-first for new product work;
- test-first for bugs and controlled implementation;
- documentation-first for public docs and repo experience;
- discovery-first for unclear product questions;
- security-first for sensitive surfaces;
- design-first for visible product experience;
- incident-first for live problems;
- release-first for promotion and rollout.

The method defines required artifacts, gates and evidence.

A worker can execute within a method. A worker does not get to invent the method.

## Gates

A gate decides whether work may advance.

Important gates include:

- Source gate: source and assumptions are separated.
- Product-definition gate: the PRD/product target is usable.
- Scope gate: meaningful requirements are accounted for.
- Method gate: process and evidence rules exist.
- Capability gate: required capability exists or failed safely.
- Architecture gate: boundaries and dependencies are understood.
- Product-experience gate: user-facing states and proof path exist.
- Security gate: risk controls and review path exist.
- Worker-result gate: the right result exists and validates.
- Human gate: human authority is required.
- Receipt Five gate: closure evidence exists.

Gates fail closed. Missing evidence blocks promotion.

## Workers

Workers are bounded specialists.

A worker may implement, review, verify, reconcile evidence, produce a security packet, prepare a release package, analyze product experience, repair an artifact or inspect documentation quality.

A worker does not own the whole route. A worker does not mark parent work done by itself. A worker does not replace Hermes state.

## Worker packet versus worker result

A worker packet is a request.

A worker result is an evidence-bearing output.

The distinction matters because a system can create many packets without any work being executed. Only a validated, consumable result can satisfy a gate.

```text
packet means: this work has been assigned
result means: this work produced output
evidence means: the output can be trusted enough to advance
```

## Reviewer separation

Executor and reviewer should be separate when risk matters.

A worker should not approve its own work. Auto-review can provide pre-landing evidence, but it is not final authority for sensitive or release-grade work.

## Human gate

A human gate is not a status update.

It is a decision package for human authority: approval, access, cost, production, funds, secrets, mainnet, material risk or product direction.

If the factory can repair or continue safely, it should not ask the operator.
