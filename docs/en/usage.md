# Usage

This page is the practical path for a local checkout. It does not pretend that a local checkout is the same as a live operator-owned Hermes runtime. It gives you a safe first proof, then shows the checks used before public documentation or claims should move.

## Requirements

You need Python 3.11 or newer and a checkout of the repository. A live Hermes runtime is optional for local kernel validation. It becomes required only when you want real operator and worker execution.

## Local doctor

```bash
cd factory
python3 scripts/factoryctl.py doctor
```

A passing doctor checks package metadata, repository shape, the minimal example, public CLI shape, and the local V3 activation proof. The command may warn that Hermes runtime was not checked. That warning is correct: local validation is not live Hermes E2E proof.

## Minimal run

```bash
cd factory
python3 scripts/factoryctl.py run minimal
```

Expected result:

```text
Wrote .tmp/quickstart-result.json
PASS: wrote .tmp/quickstart-result.json
```

This proves that the public minimal path can write a valid local proof artifact. It does not prove that a real product was delivered.

## Inspect the factory instead of guessing

Use the executable registries when you want facts:

```bash
cd factory
python3 scripts/factoryctl.py route-registry
python3 scripts/factoryctl.py method-engines
python3 scripts/factoryctl.py operating-systems
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

These commands are better than reading old prose because they come from the implementation surface.

## Build the documentation site

From the repository root:

```bash
python3 -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-site
```

The site is intentionally small: English, Portuguese, and public assets. The old technical archive is under `factory/legacy-docs/` and is not part of the main navigation.

## Public safety checks

Before changing public docs or public claims, run:

```bash
cd factory
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/validate_worker_profiles.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
python3 scripts/generate_factory_reference_docs.py --check
```

`validate_public_surface_sync.py` checks that public surfaces still match their manifest. `validate_promise_implementation_map.py` checks that public promises still have implementation and boundary references. `public_safety_scan.py` and `secret_safety_scan.py` protect the public repo boundary.

If a check fails, do not describe the public surface as ready. Fix the mismatch or state the boundary honestly.

Generated outputs under `.tmp/`, validation snapshots, pilot records, and local proof artifacts are runtime evidence. They must not be committed as public source unless a specific public contract explicitly says the artifact belongs in the repository.

## Full local validation

For a deeper local pass:

```bash
cd factory
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

This is heavier than the public smoke path, but it is the right check before a broad docs or contract change.

## Live Hermes usage

A real run requires a Hermes runtime owned by the operator. The public kernel can prepare contracts and validate local proof paths, but live cards, workers, comments, workspaces, evidence, and transitions live in Hermes.

Do not treat `doctor` or `run minimal` as proof that a product shipped. Treat them as proof that this checkout is coherent enough to start from.
