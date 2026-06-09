# Context Spine

The context spine is a controlled memory model for the factory. It is a
separate architecture decision, not a direct claim from the open-vs-closed
specialist source.

## Memory Types

| Type | Purpose | Risk |
|---|---|---|
| source memory | remember source URLs, ledgers and capture status | stale or misattributed source |
| decision memory | remember approved decisions and rejected alternatives | decision drift |
| artifact memory | remember paths to durable artifacts | private path leakage |
| worker memory | remember worker performance and repeated shapes | premature closed-worker promotion |
| risk memory | remember known hazards and mitigations | normalized risk |
| learning memory | remember pilot lessons and factory changes | overfitting to one pilot |

## Required Fields

Every memory write must include:

- source or event;
- trust tier;
- author or worker;
- timestamp;
- freshness/expiration;
- evidence refs;
- poisoning risk note;
- public/private scope.

## Rules

1. Memory is not truth by itself.
2. Private memory cannot be copied into public artifacts.
3. Source memory must distinguish source from inference.
4. Learning memory must become tests, docs, schema, worker contract or rejected
   input.
5. Any memory used to unblock work must be visible in the receipt or handoff.

## Why This Is Better

Agents need durable context, but persistent context is also an attack surface.
The spine keeps memory useful without letting old, poisoned or private context
silently become authority.
