# First External Operator Walkthrough

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: README.md, `scripts/factoryctl.py`,
> `examples/minimal-hermes-project/`, tests.
> Runtime boundary: this walkthrough proves the public factory path locally. It
> does not mutate a real Hermes board.

## Goal

This is the shortest complete run for a new operator. It starts from a fresh
clone, validates the public example, shows which gates matter and writes all
generated output under `.tmp/`.

## 1. Fresh Clone

```bash
git clone https://github.com/felipegermano17/overkill-factory.git
cd overkill-factory
python -m pip install -e .
```

## 2. Local Health Check

```bash
factoryctl doctor
overkill-quickstart
```

Expected result: quickstart prints `PASS` and writes
`.tmp/quickstart-result.json`.

## 3. Read The Minimal Product Input

The sample input is `examples/minimal-hermes-project/input-paper.md`. It is a
domain-neutral paper used to prove the factory path. It is not evidence from a
past run.

The matching card is `examples/minimal-hermes-project/card.md`.

## 4. Run The Ready Gate

```bash
factoryctl gate-report --card examples/minimal-hermes-project/card.md
```

The gate report explains:

- which workers are required;
- which worker results are still missing;
- which planning fields are present;
- whether the card can create worker tasks.

This is a planning gate, not product completion.

## 5. Generate Worker Packets

```bash
factoryctl worker-packet \
  --worker all \
  --required-only \
  --card examples/minimal-hermes-project/card.md \
  --out .tmp/external-operator-worker-packets
```

These JSON files are what an operator would hand to their runtime routing layer.
Keep them in `.tmp/`; do not commit generated packets.

## 6. Understand The Decisions

The minimal card stays honest about these boundaries:

- Product Face is required because the card has visible product surfaces.
- Independent review is required before completion.
- Receipt Five is required before done.
- Human approval is real evidence only; the factory must not invent it.
- Generated outputs remain local unless they are intentionally promoted as
  public-safe examples.

## 7. Local Release Hygiene

Before publishing a branch, run:

```bash
python scripts/validate_public_json_artifacts.py
python scripts/validate_worker_profiles.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python scripts/supply_chain_proof.py --check --no-write
python -m unittest discover -s tests -p "test_*.py" -q
```

## Next Step

Use `docs/getting-started/install-in-hermes.md` when you are ready to wire the
adapter into your own Hermes test runtime.
