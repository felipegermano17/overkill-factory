# Implementation status

This page separates local implementation from live external proof.

That boundary matters. Overkill Factory is supposed to make work easier to trust, so it must not overstate what has been proven.

## Implemented locally

The repository contains the local factory implementation and validation path:

- Python package under `factory/`;
- `factoryctl` command entry point;
- schemas and templates for factory contracts;
- adapters and Hermes-facing integration code;
- worker/capability/binding definitions;
- tests;
- public-safe examples and fixtures;
- public documentation under `docs/`;
- legacy technical documentation separated under `factory/legacy-docs/`.

Local checks can validate package health, schemas, generated/reference contracts, public surface safety, secret safety, docs build and minimal factory runs.

## Not proven by local checks alone

The remaining live proof is the full external operator loop.

Local checks do not prove the full live operator experience.

They do not prove by themselves that:

- a real Telegram/operator signal was received;
- the manager created a real FactoryRun from that signal;
- Hermes dispatched real workers in the live environment;
- no-idle woke a live stuck board;
- the manager delivered proactive progress without the operator opening Kanban;
- the operator received a live Receipt Five.

Those require external/live proof: a real manager + Hermes + worker + operator E2E run.

## Honest wording

Use precise wording:

- “Implemented locally” means code and tests exist locally.
- “Validated locally” means the named local command passed.
- “Live proof pending” means the external operator loop has not been proven yet.
- “Released” means release gates, ownership, rollback/monitoring and required approval are satisfied.

Do not call local validation “100% live autonomy.”

## Current docs/repo boundary

The public repository is being shaped as:

- root: small product entry;
- `docs/`: new public documentation;
- `factory/`: code and technical contracts;
- `factory/legacy-docs/`: old technical documentation retained only for compatibility, tests or migration reference.

This layout is part of the product experience. A new reader should not need this private chat to understand the project.
