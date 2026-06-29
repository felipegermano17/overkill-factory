# Overkill Factory documentation

Overkill Factory is a production system for agentic product work. It exists so an operator can send a rough signal and get controlled product execution instead of a fragile chat thread.

The factory does not try to make one model “smarter.” It makes the work harder to fake.

It does that by separating source from assumption, product definition from conversation, work assignment from worker result, evidence from confidence, human decisions from routine repair, and local validation from live proof.

## The short version

```text
You provide the initial signal.
The manager turns it into a controlled run.
The factory separates source, assumptions and open decisions.
The product definition / PRD becomes the target.
The method defines the gates and evidence.
Hermes stores and executes the durable work graph.
Workers produce bounded results.
The factory verifies evidence and repairs recoverable gaps.
The manager asks you only for real human decisions.
Receipt Five closes the work honestly.
```

## Read in this order

1. [Factory manual](factory-manual.md) — the complete human explanation of the system.
2. [How it works](how-it-works.md) — what happens after the operator sends the first message.
3. [Operator experience](operator-experience.md) — what the human should see, approve and receive.
4. [Product definition / PRD](product-definition.md) — how the product target is created and protected.
5. [Production process](process.md) — the stages from signal to closure.
6. [Runtime and state](runtime-and-state.md) — what Hermes owns and what the factory owns.
7. [Autonomy and no-idle](autonomy.md) — how the system keeps moving without asking “can I continue?” all the time.
8. [Method, gates and workers](method-gates-workers.md) — how route, approval and specialist work are controlled.
9. [Evidence and Receipt Five](evidence-and-receipt-five.md) — what counts as done.
10. [Security and release](security-and-release.md) — how risk, production and authority are handled.
11. [Installation and use](installation-and-use.md) — commands for local use and development.
12. [Repository layout](repository-layout.md) — why the repo is split into `docs/` and `factory/`.
13. [Examples and fixtures](examples-and-fixtures.md) — why these files exist and when they should be deleted.
14. [Terminology](terminology.md) — human names for factory concepts.
15. [Implementation status](implementation-status.md) — what is implemented locally and what still requires live proof.

Portuguese companion docs start at [pt-BR/index.md](pt-BR/index.md).

## What this documentation is not

This documentation is not an internal study archive. It is not a dump of generated artifacts. It is not a historical folder moved into public docs.

The public docs are the product explanation. Old technical material lives separately under `factory/legacy-docs/` only when it still has compatibility, validation or migration value.
