# Factory Mechanic Loop

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `agents/worker-profiles.public.json`,
> `agents/worker-registry.public.json`, `scripts/factoryctl.py`, GitHub issues
> and tests.
> Runtime boundary: This guide defines the improvement loop. It does not grant
> approval to mutate critical factory contracts.

The Factory Mechanic Loop is the factory-wide improvement protocol operated by
`skill-eval-distiller`. It studies repeated execution failures, successful
patterns, worker feedback, Hermes/runtime updates, public tool changes and
factory maturity findings, then turns them into bounded improvements.

It is not a separate executable worker. Do not create a `factory-mechanic`
profile unless the full worker promotion path passes: registry, profile,
binding, permission class, packet route, smoke and eval proof.

## Inputs

- repeated failure or success across factory runs;
- worker feedback or reviewer findings;
- Hermes, Codex or dependency update that may improve the factory;
- public-safe external source with a concrete factory implication;
- maturity audit, missing coverage register or learnback record.

## Allowed Outputs

- public-safe factory improvement issue in GitHub;
- rejection rationale when the signal is weak, one-off or unsafe;
- eval case, checklist, template, policy, skill or pack proposal;
- proposal packet for a worker, gate, adapter or methodology change.

## Issue Contract

A factory improvement issue must be concise and operational:

```md
## Problem

## Evidence / Origin

## Impact

## Proposal

## Out Of Scope

## Risk

## Validation Expected

## Human Approval Required?
```

Use links, file paths or sanitized references only when they are public-safe.
Do not paste raw historical evidence, private logs, screenshots, local paths,
private board links, secrets or chat transcripts.

## Authority Boundary

The loop may create issues, classify severity, propose ownership and draft
plans. It must not mutate critical factory state without explicit human
approval.

Human approval is required before changing:

- worker registry, profiles, bindings or permission classes;
- Hermes adapter/runtime behavior;
- security, release, approval or methodology gates;
- public release policy;
- any R3/R4 autonomy, access, budget, legal or privacy authority.

## Scope Boundary

This is a factory-wide maintenance loop. It must not create recurring
project-specific maintenance loops by default. A project-specific loop needs a
separate human-approved scope, owner, cadence, budget and stop condition.

## Cadence

Do not run this as a blind five-minute poll by default. Prefer signal-based
activation:

- after a completion audit or maturity audit;
- after repeated worker failure;
- when a Hermes/runtime update changes a real capability;
- when support, issue or review signals repeat;
- before promoting a new skill, worker or gate.

## Validation

Before landing changes to this loop, run:

```bash
python scripts/validate_worker_profiles.py
python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python -m unittest tests.test_worker_profiles tests.test_agent_reference_study_execution tests.test_open_source_docs tests.test_factoryctl -q
```
