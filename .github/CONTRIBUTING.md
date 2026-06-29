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

## Fixture And Generated Evidence Policy

Public fixtures are source material for tests, examples and contract checks.
They must be minimal, domain-neutral, public-safe and stable enough for another
operator to rerun without private context.

Generated evidence is different. Worker packets, gate reports, validation
summaries, scan summaries, screenshots, runtime logs and Receipt Five output
from an execution belong in `.tmp/`, `$RUNNER_TEMP`, release artifacts or a
private evidence store. They must not be committed as public examples or docs.

Allowed public fixtures:

- small source cards, input papers, expected flows and expected receipt examples;
- schema fixtures that prove one contract behavior at a time;
- test fixtures with placeholder identifiers and no private product, board,
  runtime, local path or operator-specific data.

Disallowed public fixtures:

- old pilot output or narrative execution history;
- generated worker packets, gate reports or scan output copied from a run;
- screenshots, raw logs, private runtime payloads or local workspace paths;
- broad fixture archives when one small domain-neutral fixture would prove the
  behavior.

## Pull Request Shape

Include:

- what changed;
- why it matters for an external operator;
- commands you ran;
- any remaining risks or follow-up issues.
