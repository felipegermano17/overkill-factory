# Installation and use

This page is the central technical entry point for local use.

## Requirements

- Python 3.11 or newer.
- A checkout of the repository.
- Optional: Hermes runtime for real board/worker execution.

## Install the local package

From the repository root:

```bash
python -m pip install ./factory
factoryctl doctor
factoryctl run minimal
```

`factoryctl doctor` checks that the package can find the expected factory assets.

`factoryctl run minimal` runs the minimal local factory path. It is a local proof, not a live operator proof.

## Development validation

From the repository root:

```bash
cd factory
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/factoryctl.py doctor
python scripts/factoryctl.py run minimal
```

Use the `factory/` directory for implementation work because scripts, schemas, templates and tests live there.

## Documentation build

From the repository root:

```bash
python -m pip install "./factory[docs]"
python -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-site
```

The public documentation source lives in `docs/`. The MkDocs config is `docs/mkdocs.yml`.

## Public-surface validation

From the repository root:

```bash
cd factory
python scripts/validate_public_json_artifacts.py
python scripts/validate_promise_implementation_map.py
python scripts/validate_public_surface_sync.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python scripts/supply_chain_proof.py --check --no-write
```

These checks protect public JSON, public documentation, promise-to-implementation coverage, secret hygiene and supply-chain proof.

## What local commands prove

Local commands prove package health, local contracts, tests, examples and documentation structure.

They do not prove the live operator path.

Live proof requires:

```text
real operator channel
-> manager-created run
-> Hermes board
-> worker dispatch
-> worker result
-> progress delivery
-> Receipt Five returned to the operator
```

## Where implementation lives

Implementation lives in `factory/`.

Important areas:

- `factory/scripts/` — CLI and validators.
- `factory/schemas/` — machine contracts.
- `factory/templates/` — run, worker and receipt templates.
- `factory/agents/` — public worker/capability/binding definitions.
- `factory/adapters/` — runtime adapters, including Hermes integration.
- `factory/tests/` — regression tests.
- `factory/examples/` — small public-safe examples with a clear purpose.
- `factory/fixtures/` — test fixtures with a clear validation purpose.
- `factory/legacy-docs/` — old technical documentation kept out of the new public docs.
