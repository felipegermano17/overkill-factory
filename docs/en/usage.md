# Usage

This page is the first practical path for a local checkout.

## Requirements

- Python 3.11 or newer.
- A checkout of this repository.
- Optional: Hermes runtime if you want live operator/worker execution. Local kernel checks do not require a live Hermes runtime.

## Local doctor

```bash
cd factory
python3 scripts/factoryctl.py doctor
```

A passing doctor checks the local package metadata, repository shape, minimal example path, public CLI surface, and V3 production-activation local proof. It may warn that Hermes runtime was not checked. That warning is honest: local validation is not live Hermes E2E proof.

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

This proves the public minimal path can materialize a valid local proof artifact.

## Build the documentation site

From the repository root:

```bash
python3 -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-site
```

The docs are written as a GitHub-first manual and are already structured for MkDocs.

## Inspect the route system

```bash
cd factory
python3 scripts/factoryctl.py route-registry
python3 scripts/factoryctl.py method-engines
python3 scripts/factoryctl.py operating-systems
```

Use these commands when you want facts from the executable surface instead of from prose.

## Compile the workflow

```bash
cd factory
python3 scripts/factoryctl.py compile-workflow --out .tmp/factory-workflow-compiled-plan.json
```

This produces the phase plan used by the lifecycle documentation.

## Public safety checks

Before changing public docs or claims, run at least:

```bash
cd factory
python3 scripts/validate_public_json_artifacts.py
python3 scripts/validate_public_surface_sync.py
python3 scripts/validate_promise_implementation_map.py
python3 scripts/public_safety_scan.py
python3 scripts/secret_safety_scan.py
```

If a check fails, do not describe the public surface as ready. Fix the mismatch or report the boundary honestly.

Generated outputs under `.tmp/`, validation snapshots, pilot records, and local proof artifacts are runtime evidence. They must not be committed as public source unless a specific public contract explicitly says the artifact is part of the repository surface.

## Live Hermes usage

A real run requires an operator-owned Hermes runtime. The public kernel can prepare and validate contracts, but live cards, workers, comments, workspaces, evidence, and transitions live in Hermes.

Do not treat `doctor` or `run minimal` as proof that a real product has shipped.
