# Quasar Vault Guard Pilot

This is the first Overkill Factory test pilot.

The pilot uses a deliberately messy raw product paper and forces the factory to
exercise the hard surfaces:

- Product Face.
- Wallet UI.
- Solana/Quasar onchain work.
- Codex Security/Cybersecurity timing.
- solanabr/Auditor path.
- Independent review.
- Human gate.
- Hermes Kanban execution.
- Receipt Five.
- Factory V3.6 learning.

## Pilot Status

`completed_dry_pilot`

This pilot proves the factory flow and contracts against a controlled test
paper. It does not ship production software, deploy a Solana program, touch
keys, touch funds, or write devnet/mainnet state.

## Main Evidence

- `00-raw-paper.md`
- `02-product-sot.md`
- `04-architecture-candidate.md`
- `05-product-face-packet.md`
- `07-onchain-work-package.md`
- `08-security-scan-packet.md`
- `10-documentation-os.md`
- `11-decomposition-card-graph.md`
- `product-face/prototype.html`
- `evidence/product-face-validation-report.md`
- `evidence/security-scan-report.md`
- `evidence/auditor-preflight-report.md`
- `evidence/independent-review-report.md`
- `evidence/human-gate-record.json`
- `evidence/receipt-five-first-slice.json`
- `evidence/worker-closure-summary.json`
- `evidence/v2-completion-gate-evidence.md`
- `evidence/hermes-kaxis-qa-review.md`
- `evidence/hermes-kaxis-security-review.md`
- `evidence/hermes-kaxis-cybersecurity-review.md`
- `evidence/hermes-kaxis-cto-review.md`
- `evidence/hermes-kaxis-reviewer-review.md`
- `12-pilot-retrospective-v3-6.md`

## Portable Verification

These commands work from inside this pilot folder:

```bash
python tools/factoryctl.py validate-card cards/qvg-first-slice.md
python tools/factoryctl.py gate-report --card cards/qvg-first-slice.md --out evidence/gate-report-first-slice.json
python tools/factoryctl.py validate-receipt evidence/receipt-five-first-slice.json
```

The portable tool exists because Hermes profile reviewers found that the
context-lock package should be independently checkable without assuming the full
repo is mounted next to it.
