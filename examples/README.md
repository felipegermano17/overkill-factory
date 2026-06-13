# Examples

Examples are small source examples and fixtures that teach or test the public
factory path.

## What Belongs Here

- Source examples that can be read, validated and rerun by a new operator.
- Minimal cards, papers, expected flows and public-safe receipt examples.
- Fixtures that support tests without storing generated proof archives.
- Expected receipt files only when they are hand-authored public fixtures, not
  copied output from a previous run.

## What Does Not Belong Here

- Do not commit generated run output.
- Generated worker packets and gate reports belong in `.tmp/`, not in this
  directory.
- Do not store old pilot evidence, private product material, screenshots,
  raw logs or local workspace paths here.
- Do not add fixture archives when a small domain-neutral fixture can prove the
  same behavior.

## Source Of Truth

`examples/minimal-hermes-project/` is the first public example. It is source
material for quickstart validation, not a record of a past run.

`examples/local-web-cockpit-factory-slice/` is the public planning slice for
the local-first Factory Web Cockpit. It proves the cockpit request enters the
factory through Product SOT, Method Contract, Product Face, security and worker
packet gates before implementation.

## How It Is Validated

Run the quickstart and public example checks:

```bash
python scripts/quickstart_smoke.py
python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
python scripts/factoryctl.py validate-card examples/local-web-cockpit-factory-slice/card.md
python -m unittest tests.test_open_source_docs -q
```
