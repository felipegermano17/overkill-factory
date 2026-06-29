# Examples

Examples are small public-safe source examples that teach or validate the factory path.

They are not generated run output, historical proof archives, private project material or old pilot evidence.

Generated worker packets and gate reports belong in `.tmp/`. Do not commit generated run output as examples.

## Current examples

| Path | Purpose |
| --- | --- |
| `minimal-hermes-project/` | First public example for quickstart validation: source paper, card, expected flow and expected Receipt Five. |
| `cards/` | Positive and negative card examples for gate/contract behavior. |
| `receipts/` | Public-safe receipt metadata examples for contract tests. |

## Keep rule

An example stays only if it has a clear reader or validator.

Good example:

- small;
- public-safe;
- understandable by a new operator;
- connected to a documented command or test;
- not copied from a private run.

Bad example:

- generated output;
- raw logs;
- local paths;
- private source;
- large archive;
- old artifact kept because it once helped a session.

## Validation

From `factory/`:

```bash
python scripts/quickstart_smoke.py
python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
python -m unittest tests.test_open_source_docs -q
```
