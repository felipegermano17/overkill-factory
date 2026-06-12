# Tests

Tests are the regression suite for the public path and contract behavior.

## What Belongs Here

- Automated regression tests for schemas, scripts, adapters, docs and the public
  quickstart.
- Tests that make public onboarding, worker routing and safety rules durable.
- Small fixtures required to reproduce contract behavior.

## What Does Not Belong Here

- Manual evidence archives, screenshots or generated proof outputs.
- Tests that rely on private local paths, private boards or operator secrets.
- Narrative validation history.

## Source Of Truth

Tests encode the public behavior the repository promises. Passing tests are not
production approval, but failing tests block publication.

## How It Is Validated

Run the full public test suite:

```bash
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/quickstart_smoke.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```
