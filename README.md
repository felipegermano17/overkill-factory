# Overkill Factory

Language: English | [Portugues](README.pt-BR.md)

Overkill Factory is a product factory operated by AI agents.

Its job is simple to say and hard to do: turn a raw human request into a verified product outcome without letting agents pretend that progress happened.

Instead of asking one agent to "build this app" and hoping it understands, plans, implements, tests, reviews and delivers correctly, the Factory turns the request into a production line:

1. preserve the source,
2. separate facts from assumptions,
3. define the product truth,
4. choose the right method for the risk,
5. split the work into bounded units,
6. dispatch specialist workers,
7. require evidence,
8. run independent review,
9. ask the human only when real authority is needed,
10. close with a Receipt Five or an honest block.

The point is not to make AI sound more organized. The point is to stop AI from producing theater: beautiful files, busy cards, confident summaries and "done" messages without proof.

## Read This First

- [Factory manual](docs/en/factory-manual.md) - the full human explanation of what the Factory is and how it works.
- [Technical reference](docs/en/technical-reference.md) - the repo, Hermes runtime model, phases, routes, workers, commands and proof boundaries.
- [Visual map](docs/assets/public-map/overkill-factory-map-v1.0.3.html) ([public copy](https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html)) - complete visual explanation built with Archify.
- [Portuguese manual](docs/pt-BR/factory-manual.md) and [technical reference](docs/pt-BR/technical-reference.md) - Portuguese mirror for operators.

## The Simple Mental Model

You are the factory owner.

The gerente is the person at the front desk who talks to you.

Hermes is the factory floor where live work, cards, sessions, workers and evidence exist.

The Kanban board is the live wall of work.

Workers are specialists.

Schemas and templates are the official forms.

Validators are inspectors.

Evidence is the receipt trail.

Human gates are real authority decisions.

Receipt Five is the final delivery receipt.

Learnback is how the Factory improves after real failures.

## What Is In This Repository

This repository contains the public kernel of the Factory.

- `docs/`: the small public documentation surface.
- `factory/`: the implementation, contracts, validators, examples, fixtures, tests and Hermes adapters.
- `docs/assets/public-map/overkill-factory-map-v1.0.3.html`: the complete visual map.

The public kernel currently exposes 26 compiled phases, 14 route classes, 8 method engines, 17 operating-system areas, 40 public workers, 251 JSON schemas, 163 JSON templates and 102 Python test files in this checkout.

Those numbers prove the repo has a structured kernel. They do not prove that a private product run was delivered.

## Quick Local Proof

From the repository root:

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

A passing local proof means the public kernel is coherent. It does not prove a live Hermes product delivery, a production deployment, a mainnet release, worker execution on a real board, or human approval.

For a real product delivery, the Factory needs live Hermes state, current cards, worker results, evidence, readback, independent review, required human gates and Receipt Five.

## The Golden Rule

Nothing is really done because an agent said it is done.

It is done only when the Factory can show what was requested, what was produced, what evidence supports it, who reviewed it, what risk remains and what final state was authorized.
