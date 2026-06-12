# Factory Mechanic Loop

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `agents/worker-profiles.public.json`,
> `agents/worker-registry.public.json`, `scripts/factoryctl.py`, GitHub issues
> and tests.
> Runtime boundary: This guide defines the improvement loop. It does not grant
> approval to mutate critical factory contracts.

The Factory Mechanic Loop is the factory-wide improvement protocol operated by
`skill-eval-distiller`. It consumes active radar signals, repeated execution
failures, successful patterns, worker feedback, Hermes/runtime updates, public
tool changes and factory maturity findings, then turns them into bounded
improvements.

It is not a separate executable worker. Do not create a `factory-mechanic`
profile unless the full worker promotion path passes: registry, profile,
binding, permission class, packet route, smoke and eval proof.

## Inputs

- repeated failure or success across factory runs;
- worker feedback or reviewer findings;
- Hermes, Codex or dependency update that may improve the factory;
- public-safe external source with a concrete factory implication;
- maturity audit, missing coverage register or learnback record.
- `factory_improvement_radar` records from the active radar pass.

## Active Radar Layer

The active layer is the Factory Improvement Radar. It is not a blind executor
and not a release authority. It is a source-watch pass that asks:

1. What changed outside or inside the factory?
2. Could that change reduce friction, improve proof, improve safety, simplify
   maintenance or strengthen open-source onboarding?
3. What could break if the factory adopts it?
4. What validation would prove adoption is safe?
5. Does this become an issue, a rejected signal, a monitor item or a human
   decision request?

Use `templates/factory-improvement-radar.json` for the radar record. The schema
lives at `schemas/factory-improvement-radar.schema.json`.

### Source Watchlist

The radar may inspect public-safe signals from:

- Hermes release notes, changelogs, issue queues or version output;
- local Hermes adapter smoke results and compatibility manifests;
- factory completion audits, Receipt Five failures and blocked-worker patterns;
- worker result notes, reviewer findings and human rejection reasons;
- GitHub issues, PRs, CI failures, dependency alerts and security scans;
- external research or public posts when they map to a concrete factory
  improvement.

### Hermes Update Example

If Hermes ships a new worker/thread orchestration feature, the radar does not
modify the adapter. It creates a signal:

- source: public Hermes release note or local version check;
- hypothesis: this may reduce manual worker routing or improve thread
  supervision;
- risk: adapter compatibility, queue drift, approval bypass, card-state
  mutation or rollback weakness;
- action: create a factory improvement issue;
- validation: disposable Hermes smoke, compatibility manifest, no-spawn safety
  check, blocked-event proof and rollback plan.

Only after that issue is reviewed can an implementation worker change the
adapter, and only with the required human gate for critical runtime behavior.

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

This loop should be active, but not noisy. Prefer signal-based activation plus
a scheduled radar pass. A practical default is weekly radar review, immediate
review for high-risk Hermes/security/runtime updates, and pre-release review
before changing worker routing, adapter behavior or gates.

Do not run a five-minute poll by default unless a human explicitly approves the
cost, source list, stop condition and allowed actions. Prefer:

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
