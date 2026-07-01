# Workers and work units

A good worker does not receive “build the product.” It receives bounded work with source, scope, authority, and proof.

## Why that matters

An autonomous agent with a vague mission expands scope, chooses shortcuts, and confuses intention with task. The Factory turns the request into small units so autonomy is useful without handing over the whole keychain.

## Good unit

A good unit has:

- input;
- output;
- owner;
- dependency;
- required evidence;
- reviewer;
- rule of done;
- authority limit.

A bad unit says only:

```text
Build onboarding.
```

## Worker Packet

Worker Packet is the task delivered to the worker.

Example:

```text
Task: fix empty-cart checkout bug.
Source: issue #123 and local reproduction.
Scope: empty-cart checkout only.
Out of scope: pricing, payment provider, auth.
Proof: test fails before, passes after.
Authority: may edit checkout and test; may not change billing.
```

## Worker Result

Worker Result is the structured return from the worker.

It must state what was done, which evidence was produced, which files changed, which tests ran, whether there is a blocker, what risk remains, and whether another worker needs a handoff.

## Authority

Workers do not decide release, mainnet, funds, secrets, waivers, or residual risk. Workers also do not review their own material work.

## Specialists

Some workers are general. Others cover security, supply chain, Product Face, evidence reconciliation, source ledger, QA, remote proof, handoff, and human-gate support.

Worker choice should come from route and method, not agent preference.

## Common failures

- planner pretending to provide implementation proof;
- builder approving its own result;
- reviewer not reading the artifact;
- worker returning file without evidence;
- capability pack assumed without coverage;
- result not consumed by the graph.

## Learning

When a worker fails repeatedly, the Factory should promote learning: new test, skill, schema, gate, doc, issue, or process change. Learnback is not a loose comment; it is improvement with proof.
