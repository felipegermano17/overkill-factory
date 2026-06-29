# Production process

This is the canonical human process from signal to closure.

The exact implementation may use schemas, scripts and adapters, but the human process should remain understandable.

## 1. Signal intake

The operator sends a signal. The manager records it and identifies the work type: new product, existing product, documentation, bug, incident, migration, release, research or continuation.

The output is not “we will do it.” The output is controlled intake.

## 2. Source boundary

The factory separates facts from assumptions.

It records:

- provided source;
- inferred assumptions;
- conflicts;
- missing source;
- safe autonomous research;
- human-only decisions.

This prevents later work from pretending inference is source.

## 3. Product definition / PRD

The factory creates or updates the product target.

The product definition includes scope, non-scope, users, journeys, requirements, acceptance examples, risks, dependencies and evidence expectations.

If the operator provides a PRD-style document, it is source. If not, the factory creates a candidate and asks for decisions only when necessary.

## 4. Scope coverage

Every meaningful requirement is accounted for before execution is treated as complete.

A requirement may be:

- planned;
- done with evidence;
- blocked;
- deferred;
- out of scope;
- human-owned;
- replaced by an approved decision.

It may not disappear silently.

## 5. Method selection

The factory chooses a method based on the work.

Examples:

- spec-first;
- test-first;
- documentation-first;
- discovery-first;
- security-first;
- design-first;
- incident-first;
- migration-first;
- release-first.

The method creates the gates and evidence rules for the run.

## 6. Domain, risk and capability routing

The factory identifies domain surfaces and risk: frontend, backend, data, docs, AI, agent runtime, Solana/onchain, payments, keys, secrets, privacy, production, security and release.

If a capability is missing, capability acquisition runs before human escalation.

## 7. Architecture, experience and security shaping

Architecture, product experience and security shape the plan before implementation.

This prevents late discovery that the system has no rollback, no security owner, no visual proof, no user-state coverage or no domain reviewer.

## 8. Product creation plan

The plan turns product definition into work units.

Each work unit has:

- requirement reference;
- owner;
- reviewer;
- dependencies;
- ready rule;
- blocked rule;
- done rule;
- evidence requirement.

## 9. Hermes materialization

Work units become Hermes/Kanban cards and dependencies.

Hermes owns runtime state and dispatch. The factory should not rely on chat memory as the source of the next action.

## 10. Worker execution

Workers execute bounded tasks.

Worker packets are assignments. Worker results are evidence-bearing outputs. The factory only advances when the result is valid and consumable.

## 11. Verification and review

The factory verifies by evidence type.

Code, UI, docs, security, release and onchain work all need different proof.

## 12. Repair and no-idle

Recoverable gaps route to repair. No-idle wakes safe next actions when the board would otherwise sit still.

The operator is not the default repair queue.

## 13. Human gates

The manager asks the operator only for real decisions.

Human gates include context, options, consequences, recommendation, evidence and safe default.

## 14. Receipt Five

Receipt Five closes the run with:

1. what changed;
2. where it lives;
3. how it was verified;
4. what reviewed it;
5. what remains.

## 15. Release, block, operate or learn

The run ends in one of four honest states:

- release: gates and evidence support release;
- block: something required is missing;
- operate: the product is live and needs monitoring/support;
- learnback: the factory itself should improve from the run.
