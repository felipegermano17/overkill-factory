# Overkill Factory

Language: English | [Português](README.pt-BR.md)

Overkill Factory is a product factory for agentic work on top of Hermes.

It turns a rough product signal into controlled factory state: source intake, source ledger, product truth, method contract, bounded work units, Hermes worker execution, evidence, review, release or block, and learnback.

The short version:

```text
Hermes runs the factory floor.
Overkill Factory defines the production method and checks.
Agents execute bounded work.
Humans decide real human gates.
Evidence decides whether work can advance.
```

## Read the documentation

The public documentation was rewritten as a product manual instead of a scattered technical archive.

- [English documentation](docs/en/index.md)
- [Documentação em português](docs/pt-BR/index.md)
- [Public visual map](https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html)

Hermes and Receipt Five remain the source of truth for runtime completion claims: the map and the manual explain the factory; they do not prove that a product was delivered.

The old public docs were preserved under `factory/legacy-docs/` for historical compatibility only. They are not the canonical source of truth.

## First local proof

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

A passing local proof means the public kernel is coherent. It does not prove that a real operator-owned Hermes runtime delivered a specific product.

## Repository shape

```text
README.md              public English entry
README.pt-BR.md        public Portuguese entry
docs/                  canonical public documentation and public catalogs
factory/               implementation, schemas, templates, workers, tests, examples, legacy docs
```

Inside `factory/`, the important public areas are `agents/`, `examples/`, `fixtures/`, `schemas/`, `scripts/`, `skills/`, `templates/` and `tests/`.

Generated worker packets and gate reports belong in `.tmp/`, not in public documentation.

## Public kernel facts

This repository currently exposes:

- 26 compiled factory phases;
- 14 route classes;
- 8 method engines;
- 17 operating-system areas;
- 40 public workers;
- 244 JSON schemas;
- 156 JSON templates;
- 97 tests.

The factual source for current behavior is the executable surface in `factory/`, especially `factory/scripts/factoryctl.py`, `factory/schemas/`, `factory/templates/`, `factory/agents/`, and `factory/tests/`.

Canonical public docs live in `docs/`; implementation and validation live in `factory/`.

Narrative validation history, roadmap archives, pilot journals and research notes do not belong in the public onboarding path. They can exist as private or legacy evidence, but the public README should point to the product manual, local proof commands, and current executable facts.
