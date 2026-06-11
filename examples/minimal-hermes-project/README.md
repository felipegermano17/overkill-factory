# Minimal Hermes Project Example

This folder is a small public-safe example for a user with their own Hermes
runtime.

Files:

- `input-paper.md`: the fictitious product paper.
- `card.md`: the runnable factory card derived from the paper.
- `expected-flow.md`: the gates and workers you should expect.
- `expected-receipt-five.json`: an example closure receipt shape.

## Run It

```bash
python scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md
python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
```

The output worker packets are assignments for Hermes profiles. They are not
proof that the workers completed the job.

## What To Look For

The card is intentionally product-facing and low-risk. A correct run should
show:

- source and Product SOT work before implementation claims;
- Product Face evidence before visible product completion;
- security and public-safety gates when the card requires them;
- independent review before completion when review is required;
- Receipt Five before `done`.

Control Tower is optional. Hermes state and receipt artifacts remain the source
of truth.
