# Contributing

Overkill Factory welcomes focused contributions that make the public factory
easier to run, inspect or integrate with Hermes.

## Before Opening A Pull Request

Run:

```bash
factoryctl doctor
factoryctl run minimal
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/validate_document_governance.py
python scripts/validate_public_json_artifacts.py
python scripts/validate_worker_profiles.py
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
python scripts/supply_chain_proof.py --check --no-write
```

## Contribution Rules

- Keep public docs about understanding and using the product.
- Keep raw validation evidence, old pilot output, screenshots and private
  operational history out of the repository.
- Add or update tests when changing schemas, worker routing, adapters or CLI
  behavior.
- Do not commit secrets, private board links, local absolute paths or private
  runtime identifiers.
- Prefer small pull requests with one clear outcome.

## Pull Request Shape

Include:

- what changed;
- why it matters for an external operator;
- commands you ran;
- any remaining risks or follow-up issues.
