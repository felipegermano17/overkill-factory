# Operator experience

The operator experience is what a human should feel when using the factory.

The factory may have many internal contracts, scripts and workers, but the operator should not be forced to watch that machinery directly. The operator should feel that the system is organized, honest and proactive.

## What the operator sends

The operator sends a signal.

A signal can be:

- a rough idea;
- a product brief;
- an existing repository;
- a broken feature;
- a release request;
- an incident;
- a migration goal;
- a screenshot or design brief;
- a document that needs to become executable work.

The signal does not need to be perfect. The factory exists to structure it.

## What the manager should do first

The manager should reply with controlled understanding, not vague enthusiasm.

A good first response says:

- what the manager understood;
- what type of work this appears to be;
- what source material was received;
- what assumptions were inferred;
- what can proceed without more input;
- what requires a human decision;
- what the next factory state is.

The manager should not expose every internal artifact. It should expose what helps the operator trust the run.

## What the operator should not have to do

The operator should not have to:

- remember the next task for the agent;
- reopen Kanban just to wake the system;
- decide internal retries;
- approve every small continuation;
- interpret raw worker logs;
- guess whether “done” has evidence;
- keep old context alive manually;
- repeat source material that is already recorded.

If the factory can continue safely, it should continue. If it cannot, it should explain exactly why.

## Progress updates

Progress updates should be human-readable.

Bad update:

```text
F12 waiting_dependency, worker packet emitted, reducer pending.
```

Better update:

```text
The product definition is approved. The factory has split the work into six units. Two can run now, one is waiting for the design proof, and one requires your approval because it affects production release.
```

The internal state can still exist. It just should not be the primary operator language.

## Human gates

A human gate is not a status update. It is a decision request.

A human gate should contain:

- the decision needed;
- why the system cannot decide alone;
- the current evidence;
- options;
- consequences;
- recommended safe default;
- what will happen after the decision.

The manager should avoid asking “can I continue?” unless continuing really depends on human authority.

## Final delivery

Final delivery should include Receipt Five:

- what changed;
- where it lives;
- how it was verified;
- what reviewed it;
- what remains.

The operator should be able to understand the result without reading every log.

## The trust contract

The operator should be able to trust three things:

1. The factory will not call a claim complete without evidence.
2. The factory will not escalate repairable internal work as a human decision.
3. The factory will clearly separate implemented local behavior from live proof that still has not happened.
