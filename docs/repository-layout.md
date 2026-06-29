# Repository layout

The repository is intentionally split into two public concepts: documentation and factory implementation.

## Root

The public root should stay small:

```text
README.md
LICENSE
.github/
docs/
factory/
```

Hidden Git/GitHub configuration may exist when required, but the visible product surface should not look like a warehouse of internal folders.

## `docs/`

`docs/` is the public human documentation.

It should explain the product clearly:

- what Overkill Factory is;
- how it works after the first signal;
- what the manager does;
- what Hermes does;
- how workers operate;
- how gates work;
- what PRD/product definition means;
- how autonomy/no-idle works;
- what Receipt Five is;
- what is implemented locally;
- what still needs live proof;
- how to install and use the package.

English is primary. Portuguese companion docs live under `docs/pt-BR/`.

## `factory/`

`factory/` is the implementation package.

It contains:

- scripts;
- schemas;
- templates;
- adapters;
- agents and worker definitions;
- skills;
- tests;
- examples;
- fixtures;
- technical contracts;
- legacy technical docs retained only when useful.

The factory folder may be technical. The root should not be.

## Legacy docs

Old documentation belongs in `factory/legacy-docs/` only when it still has technical, compatibility, validation or migration value.

Legacy docs are not the new public manual. They should not be copied into `docs/` unless the content is still true and rewritten for a new external reader.

Historical evidence, private runtime output, old pilot material and generated study artifacts should not live in the repository. If such material is needed for a run, keep it in `.tmp`, a private evidence store or an external release artifact, not in public product docs.

## Burden of proof

Every public folder needs a reason to exist.

A folder should be kept if it has a clear purpose, validation path or user value. It should be moved, merged or deleted if it exists only because it was useful during an old internal phase.

Do not reintroduce root-level `examples/`, `fixtures/`, `scripts/`, `schemas/`, `templates/`, `tests/`, `agents/` or `skills/` unless there is a deliberate product reason and a validation path.

This applies especially to examples, fixtures and old documentation.
