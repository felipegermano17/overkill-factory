# Repository reference

This page collects short-form facts for people who already understand the product and need to find things in the repo.

## Root

- `README.md`: public English entry.
- `README.pt-BR.md`: public Portuguese entry.
- `docs/`: canonical public documentation and public catalogs.
- `factory/`: implementation, scripts, schemas, templates, agents, tests, examples, fixtures, skills, and legacy docs.

## docs/

- `docs/en/`: public English docs.
- `docs/pt-BR/`: public Portuguese docs.
- `docs/factory-workflow.catalog.json`: compiled public workflow.
- `docs/promise-implementation-map.public.json`: promise-to-implementation map.
- `docs/public-surface.manifest.json`: public surface manifest.
- `docs/assets/public-map/`: public visual map.

## factory/

- `factory/scripts/factoryctl.py`: primary public CLI.
- `factory/schemas/`: JSON contracts.
- `factory/templates/`: templates and registries.
- `factory/agents/`: workers, profiles, bindings, and permission classes.
- `factory/tests/`: regressions.
- `factory/examples/`: safe examples.
- `factory/fixtures/`: public and negative fixtures.
- `factory/legacy-docs/`: preserved history, not canonical.

## Route classes

Route classes are contract IDs. Do not translate IDs when used as IDs. `product_creation` is an example: it stays that way in contracts even when the explanation is localized.

## Main registries

- `factory/templates/factory-route-registry.json`: route classes.
- `factory/templates/method-engine-registry.json`: method engines.
- `factory/templates/factory-operating-system-registry.json`: operating-system areas.
- `factory/agents/worker-registry.public.json`: public workers.

## What not to put here

Do not put generated outputs in public docs. Worker packets, gate reports, evidence archives, and private runtime results belong in `.tmp` or their runtime store, never in canonical documentation.
