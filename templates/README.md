# Templates

Templates are starter contract files paired with schemas and tests.

## What Belongs Here

- Public card, gate, receipt, plan and result templates.
- Minimal JSON or Markdown starting points that match schemas.
- Templates that help an operator create a valid factory artifact faster.

## What Does Not Belong Here

- Finished decisions, approval records or evidence from real work.
- Generated run output or private product material.
- Templates without matching schemas, tests or documentation.

## Source Of Truth

Templates are examples of valid shape. Schemas and validation scripts decide
whether an artifact is acceptable.

## How It Is Validated

Run template and schema checks:

```bash
python scripts/validate_public_json_artifacts.py
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/public_safety_scan.py
```
