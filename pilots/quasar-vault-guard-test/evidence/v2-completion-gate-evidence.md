# Hermes V2 Completion Gate Evidence

This file exists because the live Hermes Kanban still enforces the older KAXIS
V2 completion gate before a high-risk card can be marked `done`.

The approval records in the Receipt Five are scoped to the dry pilot only. They
do not approve production, deploy, devnet, mainnet, wallet signing, key access,
funds, custody, or a real Quasar program.

## Existing Evidence

- `README.md`
- `cards/qvg-first-slice.md`
- `tools/factoryctl.py`
- `evidence/gate-report-first-slice.json`
- `evidence/worker-closure-summary.json`
- `worker-results/product-face-result.json`
- `worker-results/security-scan-result.json`
- `worker-results/auditor-result.json`
- `worker-results/independent-review-result.json`
- `evidence/human-gate-record.json`
- `evidence/receipt-five-first-slice.json`
- `evidence/hermes-kaxis-qa-review.md`
- `evidence/hermes-kaxis-security-review.md`
- `evidence/hermes-kaxis-cybersecurity-review.md`
- `evidence/hermes-kaxis-cto-review.md`
- `evidence/hermes-kaxis-reviewer-review.md`

## Structured Verification

Portable commands from inside this pilot folder:

```bash
python tools/factoryctl.py validate-card cards/qvg-first-slice.md
python tools/factoryctl.py gate-report --card cards/qvg-first-slice.md --out evidence/gate-report-first-slice.json
python tools/factoryctl.py validate-receipt evidence/receipt-five-first-slice.json
```

Repo-level commands:

```bash
python scripts/factoryctl.py validate-card pilots/quasar-vault-guard-test/cards/qvg-first-slice.md
python scripts/factoryctl.py validate-receipt pilots/quasar-vault-guard-test/evidence/receipt-five-first-slice.json
python -m unittest discover -s tests -v
```

## Sandbox Invariants

- No production deployment.
- No devnet or mainnet write.
- No wallet signing.
- No secret or key access.
- No funds movement.
- No custody action.
- No Quasar program safety claim.

## Rollback

If any evidence record is missing or contradictory, keep the Hermes card out of
`done`, archive/supersede the bad card, and rerun the dry pilot from the raw
paper with the corrected contract.
