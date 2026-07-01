# Overkill Factory

Overkill Factory is a product factory for agentic work. That sentence matters. It is not a chat prompt, not a TODO list, and not a wrapper around a coding agent. It is a way to turn an unclear product signal into controlled production: source, product definition, method, work packets, Hermes execution, review, evidence, release or block, then learning.

The current public kernel is version `3.0.2`. It exposes 26 compiled phases, 14 route classes, 8 method engines, 17 operating-system areas, 40 public workers, 244 JSON schemas, 156 JSON templates, and 97 test files. Those numbers are not decoration. They are here because the manual is tied to the executable repository, not to a sales story.

## Why this exists

Most agentic work fails in boring ways. The agent starts too soon. The brief is fuzzy. The wrong worker picks up the job. A reviewer says "looks good" without replaying the evidence. A human gate becomes a vague chat question. A run is marked done because a file exists, not because the requested product is actually usable.

Overkill Factory exists to make those failures harder.

The point is not to slow agents down. The point is to make speed trustworthy. Fast work is useful only when the factory knows what the work is, who is allowed to do it, what proof is required, and what happens when the proof is missing.

## The simple picture

A request enters the factory. The factory first protects the source: what did the operator actually ask, what material exists, what is missing, and what cannot be assumed. Then it creates product truth, chooses a method, builds bounded work, sends the right workers through Hermes, checks the results, and either releases, blocks, or learns.

If that sounds like a lot, good. Product creation is a lot. The user experience should still feel simple: ask, see the state, receive clear decisions, and get proof when something is claimed as done.

## Where to read first

Read these in order:

1. [Manual](manual.md) for the human explanation.
2. [Operating model](operating-model.md) for what happens during a run.
3. [Lifecycle](lifecycle.md) for the phase-by-phase path.
4. [Trust and evidence](trust-and-evidence.md) for how the factory fights false progress.
5. [Usage](usage.md) for commands you can run now.

Engineers can then read [Technical model](technical-model.md) and [Reference](reference.md). Nontechnical readers can stop after the manual and operating model and still understand what the project is.

## First local proof

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

A passing local proof means the public kernel is coherent. It does not prove that a private product run shipped, that a live Hermes runtime is configured, or that a human approved a risky decision. The manual keeps that boundary visible on purpose.

## What changed in this documentation

The old docs were useful to maintainers, but they read like a pile of internal departments. The current docs are a product manual. The old material is preserved under `factory/legacy-docs/` for history and compatibility. The public `docs/` tree is now the canonical explanation.
