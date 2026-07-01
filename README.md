# Overkill Factory

Language: English | [Português](README.pt-BR.md)

Agents are useful. They are also very good at looking done before the work is proven.

Overkill Factory is a production system for agentic work on top of Hermes. You send a request; the factory preserves the source, turns it into scoped work, runs agents through Hermes, collects evidence, consumes review, and only calls something done when there is a receipt.

The goal is simple: move fast without turning the operator into the QA, auditor, project manager, reviewer, and detective for every agent.

## The problem

Without a factory, the operator becomes the quality system. They must check whether the agent understood the request, invented scope, tested the right behavior, consumed review, accepted risk properly, and used “done” honestly.

That can work for a tiny task. It does not work for product work, releases, security, operations, money, production, mainnet, secrets, or human authority.

## What the Factory does

It does not replace Hermes. Hermes is the live factory floor: cards, workers, dependencies, comments, attachments, blockers, and transitions.

The Factory is the production contract around that floor. It defines how a request becomes preserved source, product truth, route, method, worker packet, worker result, readback, review, human gate, and Receipt Five.

Plainly:

- the original source cannot be destroyed by an early summary;
- fact, inference, conflict, and gap stay separate;
- workers receive bounded work, not “build the product”;
- evidence must prove the actual request;
- humans enter when the authority is genuinely human;
- local proof is not live delivery proof;
- done means receipt, not confidence in the agent’s tone.

## Start here

- [English documentation](docs/en/index.md)
- [Documentação em português](docs/pt-BR/index.md)
- [Public visual map](https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html)

If you are new, read `docs/en/01-start-here.md` and then `docs/en/03-how-a-request-moves.md`.

If you operate the factory, read `docs/en/04-operator-experience.md`, `docs/en/05-evidence-and-receipts.md`, and `docs/en/06-human-decisions.md`.

If you maintain the repository, read `docs/en/10-local-validation.md`, `docs/en/11-repository-reference.md`, and `docs/en/13-maintainer-guide.md`.

## First local proof

```bash
cd factory
python3 scripts/factoryctl.py doctor
python3 scripts/factoryctl.py run minimal
```

A passing local proof means the public kernel is coherent. It does not prove that a real operator-owned Hermes runtime delivered a specific product.

## What this repository proves

The public repository proves verifiable contracts: public docs, compiled workflow, public catalogs, routes, methods, operating-system areas, schemas, templates, worker registries, examples, fixtures, scripts, and tests.

It does not prove private delivery, real human approval, live Hermes execution, production readiness, mainnet actions, funds, or operational authorization by itself. Those require current Hermes state, worker results, specific evidence, consumed review, Receipt Five, and a human gate when the risk requires one.

## Narrative validation history

Older narrative validation records, roadmap fragments, research notes, screenshots, and pilot histories do not belong in the public onboarding path. They are preserved only as legacy material when useful for audit context. The canonical reader path starts in `docs/en/index.md`, `docs/pt-BR/index.md`, and the product documentation listed above.

## Repository shape

```text
README.md              public English entry
README.pt-BR.md        public Portuguese entry
docs/                  canonical public documentation and public catalogs
factory/               implementation, schemas, templates, workers, tests, examples, legacy docs
```

Inside `factory/`, the important public areas are `agents/`, `examples/`, `fixtures/`, `schemas/`, `scripts`, `skills`, `templates`, and `tests`.

The old public docs were preserved under `factory/legacy-docs/` for historical compatibility. They are not the canonical source of truth.

## Public status

Status, counts, and proof boundaries live in `docs/en/09-status-boundaries-and-proof.md`. The current public set includes 40 public workers. Counts for phases, routes, methods, schemas, templates, and tests should be read from registries and validators, not copied into every page.

## Contributing without breaking public truth

Before opening a PR that changes public docs, run:

```bash
cd factory
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
python3 scripts/generate_factory_reference_docs.py --check
python3 -m unittest tests.test_open_source_docs -q
```

Generated worker packets, gate reports, private runtime evidence, and temporary outputs belong in `.tmp/`, not in public documentation.
