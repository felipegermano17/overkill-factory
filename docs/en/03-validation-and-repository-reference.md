# Validation and repository reference

Local validation is required. But local validation is not live Hermes E2E proof.

It proves checkout coherence, public catalog/schema agreement, documentation build, safety scans, and local contract regressions.

## Requirements

Use Python 3.11 or newer. Run commands from `factory/` unless noted.

## Doctor

```bash
cd factory
python3 scripts/factoryctl.py doctor
```

Proves the basic kernel surface is readable. It does not prove real delivery.

## Minimal run

```bash
python3 scripts/factoryctl.py run minimal
```

Expected output includes `Wrote .tmp/quickstart-result.json` and `PASS: wrote .tmp/quickstart-result.json`.

Files in `.tmp` are generated output and must not be committed.

## Public validators

```bash
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
python3 scripts/generate_factory_reference_docs.py --check
```

`validate_public_surface_sync.py` checks manifest, required phrases, links, and public boundaries. `public_safety_scan.py` prevents dangerous public claims. `secret_safety_scan.py` prevents leaks.

## MkDocs

```bash
cd ..
python3 -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-check
```

Proves navigation and documentation build. It does not prove editorial quality by itself.

## Test suite

```bash
cd factory
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

The suite may print expected negative fixtures. The final status is what matters.

## Reading failures

Manifest failure usually means missing page, missing phrase, missing source_ref, or public overclaim.

Schema failure means JSON contract drift.

Docs build failure means navigation, link, or Markdown incompatible with strict MkDocs.

Worker profile failure means registry/profile/binding/permission drift.

## When live Hermes is required

Live Hermes is required to claim real execution, current worker results, runtime state, operational decisions, or private delivery. Local validation is not live Hermes E2E proof.


---

## Repository reference

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
