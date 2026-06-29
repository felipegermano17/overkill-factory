# Context Spine

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: `scripts/factoryctl.py`, source ledgers, decision records, receipts and tests.
> Runtime boundary: Memory helps the factory remember context. Memory is not truth by itself and cannot override source, Hermes state, gates or receipts.

The context spine is the rule for using memory without letting memory become a
hidden boss.

## Simple Picture

The factory may remember useful things, but it must always know where the memory
came from, how fresh it is and whether it is allowed to affect current work.

Old memory can help. Old memory cannot approve.

## Memory Types

| Type | Purpose | Main risk |
| --- | --- | --- |
| Source memory | Remember source URLs, ledgers and capture status. | Stale or misattributed source. |
| Decision memory | Remember approved decisions and rejected alternatives. | Decision drift. |
| Artifact memory | Remember paths to durable artifacts. | Private path leakage. |
| Worker memory | Remember repeated worker performance patterns. | Promoting a weak worker too early. |
| Risk memory | Remember known hazards and mitigations. | Normalizing risk. |
| Learning memory | Remember pilot lessons and factory changes. | Overfitting to one product or run. |

## Required Fields

Every memory write must include:

- source or event;
- trust tier;
- author or worker;
- timestamp;
- freshness or expiration;
- evidence refs;
- poisoning risk note;
- public/private scope.

## Rules

1. Memory is not truth by itself.
2. Private memory cannot be copied into public artifacts.
3. Source memory must distinguish source from inference.
4. Learning memory must become tests, docs, schema, worker contract or rejected input.
5. Any memory used to unblock work must be visible in the receipt or handoff.

## Why This Matters

Agents need durable context, but persistent context is also an attack surface.
The context spine keeps memory useful without letting old, poisoned or private
context silently become authority.
