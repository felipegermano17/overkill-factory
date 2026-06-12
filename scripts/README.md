# Scripts

Scripts provide the public CLI path, validation tools and maintainer checks.

## What Belongs Here

- CLI entrypoints such as `factoryctl.py`.
- Validation scripts for cards, schemas, worker profiles, public safety and
  release readiness.
- Small maintainer utilities that are documented and covered by tests.

## What Does Not Belong Here

- One-off local automation from a private workspace.
- Scripts that depend on private paths, private boards or local credentials.
- Generated outputs. Write those to `.tmp/`.

## Source Of Truth

`scripts/factoryctl.py`, package entrypoints and tests define the supported
operator path. `factoryctl doctor`, `factoryctl init` and
`factoryctl run minimal` are the first commands. Experimental helpers must
either graduate into that path or stay clearly secondary.

## How It Is Validated

Run the script-facing bundle:

```bash
python scripts/quickstart_smoke.py
python scripts/validate_worker_profiles.py
python scripts/validate_public_json_artifacts.py
python -m unittest discover -s tests -p "test_*.py" -q
```
